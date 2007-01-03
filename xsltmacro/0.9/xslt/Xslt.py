# -*- coding: utf-8 -*-
"""
Embed the result of an xslt-transform in wiki-formatted text.

The first argument is the stylesheet specification; the second argument is
the xml-document specification; additional arguments are optional (see below).

The stylesheet and document specifications may reference attachments, files, or
url's; the full syntax is `<module>:<id>:<file>`, where module can be either
'''wiki''', '''ticket''', '''browser''', '''file''', or '''url''':
 * `wiki:<page>:<attachment>`
 * `ticket:<ticket-number>:<attachment>`
 * `browser:source:<file>``		`''(file from repository)''
 * `file:htdocs:<file>``		`''(file from project htdocs directory)''
 * `url::<url>``			`''(note the double ::)''

However, the full form is almost never necessary. There are three short forms:
 * `<id>:<file>`, where id may be either a ticket shorthand (`#<num>`),
   '''source''', '''htdocs''', '''http''' or '''https''', or the name of a wiki
   page.
 * `<file>` to refer to a local attachment named 'file'. This only works from
   within that wiki page or a ticket.
 * `<url>` to refer to a url; must be an `http://...` or `https://...` url.

The remaining arguments are optional:
 * `use_iframe` means generate an <iframe> tag instead of directly rendering
   the result (this script needs to be installed as a plugin for this to work)
 * `if_*` are all passed as attributes to the iframe with the `if_` prefix stripped
 * `xp_*` are all passed as parameters to the xsl transformer with the `xp_` prefix
   stripped

Examples:
{{{
    [[Xslt(style.xsl, data.xml)]]
}}}
(both style.xsl and data.xml are attachments on the current page).

You can use stylesheets and docs from other pages, other tickets, or other modules:
{{{
    [[Xslt(OtherPage:foo.xsl, BarPage:bar.xml)]]        # attachments on other wiki pages
    [[Xslt(base/sub:bar.xsl, foo.xml)]]                 # hierarchical wiki page
    [[Xslt(view.xsl, #3:baz.xml)]]                      # attachment on ticket #3 is data
    [[Xslt(view.xsl, ticket:36:boo.xml)]]               # attachment on ticket #36 is data
    [[Xslt(view.xsl, source:/trunk/docs/foo.xml)]]      # doc from repository
    [[Xslt(htdocs:foo/bar.xsl, data.xml)]]              # stylesheet in project htdocs dir.
    [[Xslt(view.xsl, http://test.foo.bar/bar.xml)]]     # xml in external url (only http(s) urls allowed)
}}}

Passing parameters to the transform:
{{{
    [[Xslt(style.xsl, data.xml, xp_foo="hello")]]       # pass foo="hello" to the transform
}}}

''Adapted from the Image macro that's part of trac''
"""

import os
import inspect

from trac.core import Component, implements
from trac.web.api import RequestDone
from trac.web.main import IRequestHandler
from trac.wiki.api import IWikiMacroProvider
from trac.util import http_date
from trac.versioncontrol import Node

MY_URL = '/extras/xslt'

def execute(hdf, args, env):
    # parse arguments
    # we expect the 1st and 2nd arguments to be filenames (filespecs)
    args = args.split(',')
    if len(args) < 2:
        raise Exception("Insufficient arguments.")

    stylespec = _parse_filespec(args[0].strip(), hdf, env)
    docspec   = _parse_filespec(args[1].strip(), hdf, env)
    opts      = _parse_opts(args[2:])

    if 'use_iframe' in opts:
        url = env.href(MY_URL, ss_mod=stylespec[0], ss_id=stylespec[1], ss_fil=stylespec[2],
                       doc_mod=docspec[0], doc_id=docspec[1], doc_fil=docspec[2],
                       **dict([(k, v) for k, v in opts.iteritems() if k.startswith('xp_')]))

        attrs = { 'style': 'width: 100%; margin: 0pt', 'frameborder': '0', 'scrolling': 'auto' }
        attrs.update(dict([(k[3:], v) for k, v in opts.iteritems() if k.startswith('if_')]))

        return """
          <script type="text/javascript">
          function maximizeIframe(iframe) {
            iframe.style.scrolling = 'no'
            if (iframe.contentDocument)         // Netscape/Mozilla/Firefox
                docHeight = iframe.contentDocument.body.scrollHeight
            else                                // Exploder
                docHeight = iframe.document.body.scrollHeight
            iframe.style.height    = docHeight + 'px'
          }
          </script>
          <iframe src="%(src)s" onload="maximizeIframe(this)" %(attrs)s></iframe>
          """ % { 'src': url, 'attrs': ' '.join([ k + '="' + str(v) + '"' for k,v in attrs.iteritems() ]) }

    else:
        style_obj = _get_obj(env, hdf, *stylespec)
        doc_obj   = _get_obj(env, hdf, *docspec)
        params    = dict([(_to_str(k[3:]), _to_str(v)) for k, v in opts.iteritems() if k.startswith('xp_')])

        try:
            page, ct  = _transform(style_obj, doc_obj, params)
        finally:
            _close_obj(style_obj)
            _close_obj(doc_obj)

        return page

def _parse_opts(args):
    s_opts = ['use_iframe']     # simple opts (no value)
    v_opts = []                 # valued opts
    p_opts = ['if_', 'xp_']     # prefixed opts

    opts = {}
    for arg in args:
        parts = arg.strip().split('=', 1)
        name = parts[0].strip()
        if _has_prefix(name, p_opts):
            opts[name] = len(parts) == 2 and parts[1].strip() or ''
        elif name in s_opts:
            if len(parts) == 1:
                opts[name] = ''
            else:
                raise Exception("option '%s' does not take a value" % name)
        elif name in v_opts:
            if len(parts) == 2:
                opts[name] = parts[1].strip()
            else:
                raise Exception("option '%s' requires a value" % name)
        else:
            raise Exception("unknown option '%s'" % name)

    return opts

def _has_prefix(name, pfx_list):
    for pfx in pfx_list:
        if name.startswith(pfx): return True

    return False

def _to_str(obj):
    if isinstance(obj, str):
        return obj

    if isinstance(obj, unicode):
        return obj.encode('utf-8')

    return str(obj)

def _parse_filespec(filespec, hdf, env):
    # parse filespec argument to get module and id if contained.
    if filespec[:5] == 'http:' or filespec[:6] == 'https:':
        parts = [ 'url', '', filespec ]
    else:
        parts = filespec.split(':', 2)

    if len(parts) == 3:                 # module:id:attachment
        if parts[0] in ['wiki', 'ticket', 'browser', 'file', 'url']:
            module, id, file = parts
        else:
            raise Exception("unknown module %s" % parts[0])

    elif len(parts) == 2:
        from trac.versioncontrol.web_ui import BrowserModule
        try:
            browser_links = [link for link,_ in
                             BrowserModule(env).get_link_resolvers()]
        except Exception:
            browser_links = []

        id, file = parts
        if id in browser_links:         # source:path
            module = 'browser'
        elif id and id[0] == '#':       # #ticket:attachment
            module = 'ticket'
            id = id[1:]
        elif id == 'htdocs':            # htdocs:path
            module = 'file'
        else:                           # WikiPage:attachment
            module = 'wiki'

    elif len(parts) == 1:               # attachment
        # determine current object
        # FIXME: should be retrieved from the formatter...
        # ...and the formatter should be provided to the macro
        file = filespec
        module, id = 'wiki', 'WikiStart'
        path_info = hdf.getValue('HTTP.PathInfo', "").split('/',2)
        if len(path_info) > 1:
            module = path_info[1]
        if len(path_info) > 2:
            id = path_info[2]
        if module not in ['wiki', 'ticket']:
            raise Exception('Cannot reference local attachment from here')

    else:
        raise Exception('No filespec given')

    return module, id, file

def _get_obj(env, hdf, module, id, file):
    """Returns a filename (str or unicode), a trac browser Node, or a urllib 
       addinfourl.
    """

    # check permissions first
    if module == 'wiki'    and not hdf.has_key('trac.acl.WIKI_VIEW')   or \
       module == 'ticket'  and not hdf.has_key('trac.acl.TICKET_VIEW') or \
       module == 'file'    and not hdf.has_key('trac.acl.FILE_VIEW')   or \
       module == 'browser' and not hdf.has_key('trac.acl.BROWSER_VIEW'):
        raise Exception('Permission denied: %s' % module)

    obj = None

    if module == 'browser':
        from trac.versioncontrol.web_ui import get_existing_node
        repos = env.get_repository(hdf.get('trac.authname'))
        obj   = get_existing_node(env, repos, file, None)

    elif module == 'file':
        import re
        file = re.sub('[^a-zA-Z0-9._/-]', '', file)     # remove forbidden chars
        file = re.sub('^/+', '', file)                  # make sure it's relative
        file = os.path.normpath(file)                   # resolve ..'s
        if file.startswith('..'):                       # don't allow above doc-root
            raise Exception("illegal path '%s'" % file)

        if id != 'htdocs':
            raise Exception("unsupported file id '%s'" % id)

        obj = os.path.join(env.get_htdocs_dir(), file)

    elif module == 'wiki' or module == 'ticket':
        from trac.attachment import Attachment
        attachment = Attachment(env, module, id, file)
        obj = attachment.path

    elif module == 'url':
        import urllib

        if id:
            raise Exception("unsupported url id '%s'" % id)

        try:
           obj = urllib.urlopen(file)
        except Exception, e:
            raise Exception('Could not read from url "%s": %s' % (file, e))

    else:
        raise Exception("unsupported module '%s'" % module)

    return obj

def _close_obj(obj):
    if hasattr(obj, 'close') and callable(obj.close):
        obj.close()

def _obj_tostr(obj):
    if isinstance(obj, str) or isinstance(obj, unicode):
        return obj
    if isinstance(obj, Node):
        return obj.path
    if hasattr(obj, 'url'):
        return obj.url
    return str(obj)

def _transform(style_obj, doc_obj, params):
    import libxslt

    try:
        styledoc = _parse_xml(style_obj)
    except Exception, e:
        raise Exception("Error parsing %s: %s" % (_obj_tostr(style_obj), e))

    try:
        doc = _parse_xml(doc_obj)
    except Exception, e:
        styledoc.freeDoc()
        raise Exception("Error parsing %s: %s" % (_obj_tostr(doc_obj), e))

    style = libxslt.parseStylesheetDoc(styledoc)
    if not style:
        styledoc.freeDoc()
        doc.freeDoc()
        raise Exception("%s is not a valid stylesheet" % _obj_tostr(style_obj))

    result = style.applyStylesheet(doc, params)
    try:
        output = style.saveResultToString(result)
    except Exception, e:
        # detect empty result doc
        if str(e) != 'error return without exception set':
            raise e
        output = ''

    if result.get_type() == 'document_xml':
        ct = 'text/xml'
    elif result.get_type() == 'document_html':
        ct = 'text/html'
    elif result.get_type() == 'document_text':
        ct = 'text/plain'
    else:
        ct = 'application/octet-stream'

    style.freeStylesheet()
    doc.freeDoc()
    result.freeDoc()

    return output, ct

def _parse_xml(obj):
    import libxml2

    if isinstance(obj, str) or isinstance(obj, unicode):
        return libxml2.parseFile(obj)
    if isinstance(obj, Node):
        return libxml2.parseDoc(obj.get_content().read())
    if hasattr(obj, 'read') and callable(obj.read):
        return libxml2.parseDoc(obj.read())

    raise Exception("unsupported object type '%s'" % type(obj))

class XsltProcessor(Component):
    implements(IWikiMacroProvider, IRequestHandler)

    # IWikiMacroProvider interface

    def get_macros(self):
        yield 'Xslt'

    def get_macro_description(self, name):
        return inspect.getdoc(inspect.getmodule(self))

    def render_macro(self, req, name, content):
        return execute(req.hdf, content, self.env)

    # IRequestHandler interface

    def match_request(self, req):
        return req.path_info == MY_URL

    def process_request(self, req):
        stylespec = (req.args.get('ss_mod'), req.args.get('ss_id'), req.args.get('ss_fil'))
        docspec   = (req.args.get('doc_mod'), req.args.get('doc_id'), req.args.get('doc_fil'))
        if not stylespec[0] or not stylespec[1] or not stylespec[2] or \
           not docspec[0] or not docspec[1] or not docspec[2]:
            raise TracError('Bad request')

        style_obj = _get_obj(self.env, req.hdf, *stylespec)
        doc_obj   = _get_obj(self.env, req.hdf, *docspec)
        params    = dict([(k[3:], req.args.get(k)) for k in req.args.keys() if k.startswith('xp_')])

        lastmod = max(self._get_last_modified(style_obj),
                      self._get_last_modified(doc_obj))

        req.check_modified(lastmod)
        if not req.get_header('If-None-Match'):
            if http_date(lastmod) == req.get_header('If-Modified-Since'):
                req.send_response(304)
                req.end_headers()
                _close_obj(style_obj)
                _close_obj(doc_obj)
                raise RequestDone
        if hasattr(req, '_headers'):    # 0.9 compatibility
            req._headers.append(('Last-Modified', http_date(lastmod)))
        else:
            req.send_header('Last-Modified', http_date(lastmod))

        try:
            page, content_type = _transform(style_obj, doc_obj, params)
        finally:
            _close_obj(style_obj)
            _close_obj(doc_obj)

        req.send_response(200)
        req.send_header('Content-Type', content_type + ';charset=utf-8')
        req.send_header('Content-Length', len(page))
        if hasattr(req, '_headers'):    # 0.9 compatibility
            for name, value in req._headers:
                req.send_header(name, value)
            req._send_cookie_headers()
        req.end_headers()

        if req.method != 'HEAD':
            req.write(page)

        raise RequestDone

    def _get_last_modified(self, obj):
        import time

        if isinstance(obj, str) or isinstance(obj, unicode):
            return os.stat(obj).st_mtime
        if isinstance(obj, Node):
            return obj.get_last_modified()
        if hasattr(obj, 'info') and callable(obj.info):
            lm = obj.info().getdate('Last-modified')
            if lm:
                return time.mktime(lm)
        return time.time()

