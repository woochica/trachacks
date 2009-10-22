""" ServerSideRedirectPlugin for Trac

    Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
    This is Free Software under the BSD or GPL v3 or later license.
    $Id$
"""
__revision = r'$Rev$'[6:-2]
__date     = r'$Date$'[7:-2]
__author   = r'$Author$'[9:-2]
__url      = r'$URL$'[6:-2]


from trac.core      import  *
from trac.web.api   import IRequestHandler,IRequestFilter,RequestDone
from trac.wiki.api  import IWikiMacroProvider
from trac.mimeview.api import Context
from tracextracturl import extract_url
from trac.wiki.macros import WikiMacroBase
import re

MACRO = re.compile(r'.*\[\[redirect\((.*)\)\]\]')

class ServerSideRedirectPlugin(WikiMacroBase):
    """ This Trac plug-in implements a server sided redirect functionality.

    == Description ==
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
    }}}
    Any other [TracLinks TracLink] can be used:
    {{{
    [[redirect(wiki:OtherWikiPage)]]
    [[redirect(source:/trunk/file.py)]]
    [[redirect(http://www.example.com/)]]
    }}}
    """
    implements ( IRequestHandler, IRequestFilter, IWikiMacroProvider )

    redirect_target = ''

    def expand_macro(self, formatter, name, content):
        """Print redirect notice after edit."""
        from genshi.builder import tag
        from trac.wiki.formatter import format_to_oneliner

        if content.find(':') == -1:
          content = 'wiki:' + content

        return tag.div( tag.strong('This page redirects to: '),
                    format_to_oneliner(self.env, formatter.context, content),
                    class_ = 'system-message', id = 'notice' )

    def get_macros(self):
        """Provide but do not redefine the 'redirect' macro."""
        if self.env.config.get('components','redirect.*') == 'enabled':
            yield ''
        else:
            yield 'redirect'

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
        from genshi.builder import tag
        if self.redirect_target or self._check_redirect(req):
            target = self.redirect_target
            #self.log.debug("target = " + target)

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
        if req.path_info == '/wiki' or req.path_info == '/':
          wiki = 'WikiStart'
        elif not req.path_info.startswith('/wiki/'):
          return False
        else:
          wiki = req.path_info[6:]
        self.log.debug("SSR: wiki = " + wiki)

        # Extract Wiki page
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        if req.args.has_key('version'):
          cursor.execute("SELECT text FROM wiki WHERE name=%s and version=%s;" , (wiki,req.args['version']))
        else:
          cursor.execute("SELECT text,MAX(version) FROM wiki WHERE name=%s;" , (wiki,))
        text = cursor.fetchone();
        # If not exist or empty:
        if not text or not text[0]:
	    self.log.debug("SSR: wiki does not exists or is empty")
            return False
        text = text[0]

        # Check for redirect "macro":
        m = MACRO.match(text)
        if not m:
	    self.log.debug("SSR: wiki does not hold redirect macro" + text)
            return False
        wikitarget = m.groups()[0]
        self.redirect_target = extract_url(self.env, Context.from_request(req), wikitarget)
        if not self.redirect_target:
          self.redirect_target = req.href.wiki(wikitarget)
        self.log.debug("SSR: Redirect Target = " + self.redirect_target)
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
        self.log.debug("SSR: method = " + req.method)
        self.log.debug("SSR: path = " + req.path_info)
        args = req.args

        if isinstance(handler, WikiModule) \
           and \
           ( req.path_info.startswith('/wiki/') \
             or req.path_info == '/wiki' \
             or req.path_info == '/' \
           ) \
           and req.method == 'GET' \
           and not args.has_key('action') \
           and not args.has_key('version') \
           and (not args.has_key('redirect') or args['redirect'].lower() != 'no') \
           and req.environ.get('HTTP_REFERER','').find('action=edit') == -1 \
           and self._check_redirect(req):
                return self
        self.log.debug("SSR: No redirect.")
        return handler

    def post_process_request(self, req, template, data, content_type):
        return (template, data, content_type)

