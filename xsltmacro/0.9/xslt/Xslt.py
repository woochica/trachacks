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
 * `use_object` is just like `use_iframe` except that it uses an <object> tag
   instead of an <iframe> tag
 * `if_*` are all passed as attributes to the <iframe> tag with the `if_` prefix stripped
 * `obj_*` are all passed as attributes to the <object> tag with the `obj_` prefix stripped
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
import threading
import re
import libxml2

from trac.core import Component, implements, TracError
from trac.web.api import RequestDone
from trac.web.main import IRequestHandler
from trac.wiki.api import IWikiMacroProvider
from trac.util import http_date
from trac.versioncontrol import Node

MY_URL = '/extras/xslt'
tl     = threading.local()

def resolver(URL, ID, ctxt):
    scheme = URL.split(':', 2)[0]
    if scheme not in ['wiki', 'ticket', 'browser', 'file']:
        return None

    auth, path = re.match('[^:]*://([^/]*)/(.*)', URL).group(1, 2)
    obj = _get_src(tl.env, tl.hdf, scheme, auth.replace('%2F', '/'), path)
    return obj.getStream()

libxml2.setEntityLoader(resolver)


def execute(hdf, args, env):
    # parse arguments
    # we expect the 1st and 2nd arguments to be filenames (filespecs)
    args = args.split(',')
    if len(args) < 2:
        raise Exception("Insufficient arguments.")

    stylespec = _parse_filespec(args[0].strip(), hdf, env)
    docspec   = _parse_filespec(args[1].strip(), hdf, env)
    opts      = _parse_opts(args[2:])

    if 'use_iframe' in opts or 'use_object' in opts:
        url = env.href(MY_URL, ss_mod=stylespec[0], ss_id=stylespec[1], ss_fil=stylespec[2],
                       doc_mod=docspec[0], doc_id=docspec[1], doc_fil=docspec[2],
                       **dict(_get_opts(opts, 'xp_', False)))

        res = """
          <script type="text/javascript">
          function maximizeFrame(frame) {
            frame.style.scrolling = 'no'
            if (frame.contentDocument)         // Netscape/Mozilla/Firefox
                docHeight = frame.contentDocument.body.scrollHeight
            else                                // Exploder
                docHeight = frame.document.body.scrollHeight
            frame.style.height    = docHeight + 'px'
          }
          </script>
         """

        if 'use_iframe' in opts:
            attrs = { 'style': 'width: 100%; margin: 0pt', 'frameborder': '0', 'scrolling': 'auto' }
            attrs.update(_get_opts(opts, 'if_'))

            res += """
              <iframe src="%(src)s" onload="maximizeFrame(this)" %(attrs)s></iframe>
              """ % { 'src': url,
                      'attrs': ' '.join([ k + '="' + str(v) + '"' for k,v in attrs.iteritems() ]) }

        if 'use_object' in opts:
            attrs = { 'style': 'width: 100%; margin: 0pt' }
            attrs.update(_get_opts(opts, 'obj_'))

            res += """
              <object data="%(src)s" type="text/html" onload="maximizeFrame(this)" %(attrs)s></object>
              """ % { 'src': url,
                      'attrs': ' '.join([ k + '="' + str(v) + '"' for k,v in attrs.iteritems() ]) }

        return res

    else:
        style_obj = _get_src(env, hdf, *stylespec)
        doc_obj   = _get_src(env, hdf, *docspec)
        params    = dict(_get_opts(opts, 'xp_'))

        page, ct  = _transform(style_obj, doc_obj, params, env, hdf)

        return page

def _parse_opts(args):
    s_opts = ['use_iframe', 'use_object']       # simple opts (no value)
    v_opts = []                                 # valued opts
    p_opts = ['if_', 'obj_', 'xp_']             # prefixed opts

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

def _transform(style_obj, doc_obj, params, env, hdf):
    import libxslt

    tl.env = env
    tl.hdf = hdf

    doc    = None
    style  = None;
    result = None;

    try:
        try:
            doc = _parse_xml(doc_obj)
        except Exception, e:
            raise Exception("Error parsing %s: %s" % (doc_obj, e))

        try:
            styledoc = _parse_xml(style_obj)
        except Exception, e:
            raise Exception("Error parsing %s: %s" % (style_obj, e))

        style = libxslt.parseStylesheetDoc(styledoc)
        if not style:
            styledoc.freeDoc()
            raise Exception("%s is not a valid stylesheet" % style_obj)

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

    finally:
        if doc:    doc.freeDoc()
        if style:  style.freeStylesheet()
        if result: result.freeDoc()
        tl.env = None
        tl.hdf = None

    return output, ct

def _parse_xml(obj):
    if obj.isFile():
        return libxml2.parseFile(obj.getFile())
    else:
        return libxml2.readDoc(obj.getStream().read(), obj.getUrl(), None, 0)

def _get_src(env, hdf, module, id, file):
    # check permissions first
    if module == 'wiki'    and not hdf.has_key('trac.acl.WIKI_VIEW')   or \
       module == 'ticket'  and not hdf.has_key('trac.acl.TICKET_VIEW') or \
       module == 'file'    and not hdf.has_key('trac.acl.FILE_VIEW')   or \
       module == 'browser' and not hdf.has_key('trac.acl.BROWSER_VIEW'):
        raise Exception('Permission denied: %s' % module)

    if module == 'browser':
        return BrowserSource(env, hdf, file)
    if module == 'file':
        return FileSource(env, id, file)
    if module == 'wiki' or module == 'ticket':
        return AttachmentSource(env, module, id, file)
    if module == 'url':
        return UrlSource(file)

    raise Exception("unsupported module '%s'" % module)

def _get_opts(opts, prefix, strip_prefix=True):
    off = strip_prefix and len(prefix) or 0
    return ((_to_str(k)[off:], _to_str(opts[k])) \
                                for k in opts if k.startswith(prefix))

class TransformSource(object):
    """Represents the source of an input (stylesheet or xml-doc) to the transformer"""

    def __init__(self, module, id, file, obj):
        self.module = module
        self.id     = id
        self.file   = file
        self.obj    = obj

    def isFile(self):
        return False

    def getFile(self):
        return None

    def getUrl(self):
        return "%s://%s/%s" % (self.module, self.id.replace("/", "%2F"), self.file)

    def get_last_modified(self):
        import time
        return time.time()

    def __str__(self):
        return str(self.obj)

    def __del__(self):
        if self.obj and hasattr(self.obj, 'close') and callable(self.obj.close):
            self.obj.close()

    class CloseableStream(object):
        """Implement close even if underlying stream doesn't"""

        def __init__(self, stream):
            self.stream = stream

        def read(self, len=None):
            return self.stream.read(len)

        def close(self):
            if hasattr(self.stream, 'close') and callable(self.stream.close):
                self.stream.close()

class BrowserSource(TransformSource):
    def __init__(self, env, hdf, file):
        from trac.versioncontrol.web_ui import get_existing_node
        repos = env.get_repository(hdf.get('trac.authname'))
        obj   = get_existing_node(env, repos, file, None)

        TransformSource.__init__(self, "browser", "source", file, obj)

    def getStream(self):
        return self.CloseableStream(self.obj.get_content())

    def __str__(self):
        return self.obj.path

    def get_last_modified(self):
        return self.obj.get_last_modified()

class FileSource(TransformSource):
    def __init__(self, env, id, file):
        file = re.sub('[^a-zA-Z0-9._/-]', '', file)     # remove forbidden chars
        file = re.sub('^/+', '', file)                  # make sure it's relative
        file = os.path.normpath(file)                   # resolve ..'s
        if file.startswith('..'):                       # don't allow above doc-root
            raise Exception("illegal path '%s'" % file)

        if id != 'htdocs':
            raise Exception("unsupported file id '%s'" % id)

        obj = os.path.join(env.get_htdocs_dir(), file)

        TransformSource.__init__(self, "file", id, file, obj)

    def isFile(self):
        return True

    def getFile(self):
        return self.obj

    def getStream(self):
        import urllib
        return urllib.urlopen(self.obj)

    def get_last_modified(self):
        return os.stat(self.obj).st_mtime

    def __str__(self):
        return self.obj

class AttachmentSource(TransformSource):
    def __init__(self, env, module, id, file):
        from trac.attachment import Attachment
        obj = Attachment(env, module, id, file)

        TransformSource.__init__(self, module, id, file, obj)

    def getStream(self):
        return self.obj.open()

    def get_last_modified(self):
        return os.stat(self.obj.path).st_mtime

    def __str__(self):
        return self.obj.path

class UrlSource(TransformSource):
    def __init__(self, url):
        import urllib
        try:
            obj = urllib.urlopen(url)
        except Exception, e:
            raise Exception('Could not read from url "%s": %s' % (file, e))

        TransformSource.__init__(self, "url", None, url, obj)

    def getStream(self):
        return self.obj

    def getUrl(self):
        return self.file

    def get_last_modified(self):
        import time

        lm = self.obj.info().getdate('Last-modified')
        if lm:
            return time.mktime(lm)
        return time.time()

    def __str__(self):
        return self.obj.url

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
        if None in stylespec or None in docspec:
            self.env.log.error("Missing request parameters: %s", req.args)
            raise TracError('Bad request')

        style_obj = _get_src(self.env, req.hdf, *stylespec)
        doc_obj   = _get_src(self.env, req.hdf, *docspec)
        params    = dict(_get_opts(req.args, 'xp_'))

        lastmod = max(style_obj.get_last_modified(),
                      doc_obj.get_last_modified())

        req.check_modified(lastmod)
        if not req.get_header('If-None-Match'):
            if http_date(lastmod) == req.get_header('If-Modified-Since'):
                req.send_response(304)
                req.end_headers()
                raise RequestDone
        if hasattr(req, '_headers'):    # 0.9 compatibility
            req._headers.append(('Last-Modified', http_date(lastmod)))
        else:
            req.send_header('Last-Modified', http_date(lastmod))

        page, content_type = _transform(style_obj, doc_obj, params, self.env, req.hdf)

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

