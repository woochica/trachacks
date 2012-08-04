# -*- coding: utf-8 -*-
""" ServerSideRedirectPlugin for Trac

    Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
    This is Free Software under the BSD or GPL v3 or later license.
    $Id$
"""

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = ur"$Rev$"[6:-2]
__date__     = ur"$Date$"[7:-2]

from  trac.core          import  *
from  trac.web.api       import  IRequestHandler, IRequestFilter, RequestDone
from  trac.wiki.api      import  IWikiMacroProvider
from  trac.mimeview.api  import  Context
from  trac.wiki.model    import  WikiPage
from  genshi.builder     import  tag
import re

from  tracextracturl.extracturl import  extract_url

MACRO = re.compile(r'.*\[\[[rR]edirect\((.*)\)\]\]')

class ServerSideRedirectPlugin(Component):
    """This Trac plug-in implements a server sided redirect functionality.
The user interface is the wiki macro `Redirect` (alternativly `redirect`).

== Description ==
Website: http://trac-hacks.org/wiki/ServerSideRedirectPlugin

`$Id$`

This plug-in allow to place a redirect macro at the start of any wiki
page which will cause an server side redirect when the wiki page is
viewed.

This plug-in is compatible (i.e. can be used) with the client side
redirect macro TracRedirect but doesn't depend on it. Because the
redirect is caused by the server (using a HTTP redirect request to the
browser) it is much faster and less noticeable for the user. The
back-link feature of TracRedirect can also be used for server side
redirected pages because both generate the same URL attributes.

To edit a redirecting wiki page access its URL with `?action=edit`
appended. To view the page either use `?action=view`, which will print
the redirect target (if TracRedirect isn't active, which will redirect
the wiki using client side code), or `?redirect=no` which disables
redirection of both the ServerSideRedirectPlugin and TracRedirect
plug-in.

Direct after the redirect target is added (or modified) Trac will
automatically reload it, as it does with all wiki pages. This plug-in
will detect this and not redirect but display the wiki page with the
redirect target URL printed to provide feedback about the successful
change. However, further visits will trigger the redirect.

== Usage Examples ==
The following 'macro' at the begin of the wiki page will cause a
redirect to the ''!OtherWikiPage''.
{{{
[[redirect(OtherWikiPage)]]
[[Redirect(OtherWikiPage)]]
}}}
Any other [TracLinks TracLink] can be used:
{{{
[[redirect(wiki:OtherWikiPage)]]
[[Redirect(wiki:OtherWikiPage)]]
[[redirect(source:/trunk/file.py)]]
[[Redirect(source:/trunk/file.py)]]
[[redirect(http://www.example.com/)]]
[[Redirect(http://www.example.com/)]]
}}}
    """
    implements ( IRequestHandler, IRequestFilter, IWikiMacroProvider )

    redirect_target = ''

    def expand_macro(self, formatter, name, content):
        """Print redirect notice after edit."""

        target = extract_url(self.env, formatter.context, content)
        if not target:
          target = formatter.context.req.href.wiki(content)

        return tag.div(
                  tag.strong('This page redirects to: '),
                  tag.a(content, href=target),
                  class_ = 'system-message',
                  id = 'notice'
               )

    def get_macros(self):
        """Provide but do not redefine the 'redirect' macro."""
        get = self.env.config.get
        if get('components','redirect.*') == 'enabled' or \
           get('components','redirect.redirect.*') == 'enabled' or \
           get('components','redirect.redirect.tracredirect') == 'enabled':
            return ['Redirect',]
        else:
            return ['redirect','Redirect']

    def get_macro_description(self,name):
        if name == 'Redirect':
          return self.__doc__
        else:
          return "See macro `Redirect`."

    def match_request(self, req):
        """Only handle request when selected from `pre_process_request`."""
        return False

    def split_link(self, target):
        """Split a target along "?" and "#" in `(path, query, fragment)`."""
        query = fragment = ''
        idx = target.find('#')
        if idx >= 0:
            target, fragment = target[:idx], target[idx:]
        idx = target.find('?')
        if idx >= 0:
            target, query = target[:idx], target[idx:]
        return (target, query, fragment)

   # IRequestHandler methods
    def process_request(self, req):
        """Redirect to pre-selected target."""
        if self.redirect_target or self._check_redirect(req):
            target = self.redirect_target

            # Check for self-redirect:
            if target and target == req.href(req.path_info):
                message = tag.div('Please ',
                     tag.a( "change the redirect target",
                            href = target + "?action=edit" ),
                     ' to another page.',
                     class_ = "system-message")
                data = { 'title':"Page redirects to itself!",
                         'message':message,
                         'type':'TracError',
                       }
                req.send_error(data['title'], status=409, env=self.env, data=data)
                raise RequestDone

            # Check for redirect pair, i.e. A->B, B->A
            if target and target == req.href.wiki(req.args.get('redirectedfrom','')):
                message = tag.div('Please change the redirect target from either ',
                     tag.a( "this page", href = req.href(req.path_info, action="edit")),
                     ' or ',
                     tag.a( "the redirecting page", href = target + "?action=edit" ),
                     '.',
                     class_ = "system-message")
                data = { 'title':"Redirect target redirects back to this page!",
                         'message':message,
                         'type':'TracError',
                       }
                req.send_error(data['title'], status=409, env=self.env, data=data)
                raise RequestDone

            # Add back link information for internal links:
            if target and target[0] == '/':
                redirectfrom =  "redirectedfrom=" + req.path_info[6:]
                # anchor should be the last in url
                # according to http://trac.edgewall.org/ticket/8072
                tgt, query, anchor= self.split_link(target)
                if not query:
                    query  = "?" + redirectfrom
                else:
                    query += "&" + redirectfrom
                target = tgt + query + anchor
            req.redirect(target)
            raise RequestDone
        raise TracError("Invalid redirect target!")

    def _check_redirect(self, req):
        """Checks if the request should be redirected."""
        if req.path_info == '/' or req.path_info == '/wiki':
          wiki = 'WikiStart'
        elif not req.path_info.startswith('/wiki/'):
          return False
        else:
          wiki = req.path_info[6:]

        wp = WikiPage(self.env, wiki, req.args.get('version'))

        if not wp.exists:
            return False

        # Check for redirect "macro":
        m = MACRO.match(wp.text)
        if not m:
            return False
        wikitarget = m.groups()[0]
        self.redirect_target = extract_url(self.env, Context.from_request(req), wikitarget)
        if not self.redirect_target:
          self.redirect_target = req.href.wiki(wikitarget)
        return True


   # IRequestFilter methods
    """Extension point interface for components that want to filter HTTP
    requests, before and/or after they are processed by the main handler."""

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.

        Always returns the request handler, even if unchanged.
        """
        from trac.wiki.web_ui import WikiModule
        args = req.args

        if not isinstance(handler, WikiModule):
           return handler
        if not req.path_info.startswith('/wiki/') and not req.path_info == '/wiki' and not req.path_info == '/':
           self.env.log.debug("SSR: no redirect: Path is not a wiki path")
           return handler
        if req.method != 'GET':
           self.env.log.debug("SSR: no redirect: No GET request")
           return handler
        if 'action' in args:
           self.env.log.debug("SSR: no redirect: action=" + args['action'])
           return handler
        if args.has_key('version'):
           self.env.log.debug("SSR: no redirect: version=...")
           return handler
        if args.has_key('redirect') and args['redirect'].lower() == 'no':
           self.env.log.debug("SSR: no redirect: redirect=no")
           return handler
        if req.environ.get('HTTP_REFERER','').find('action=edit') != -1:
           self.env.log.debug("SSR: no redirect: HTTP_REFERER includes action=edit")
           return handler
        if self._check_redirect(req):
           self.env.log.debug("SSR: redirect!")
           return self
        self.env.log.debug("SSR: no redirect: No redirect macro found.")
        return handler

    def post_process_request(self, req, template, data, content_type):
        return (template, data, content_type)

