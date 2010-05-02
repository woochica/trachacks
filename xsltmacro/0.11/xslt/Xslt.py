# -*- coding: utf-8 -*-

import os
import threading
import re
import libxml2

from trac.core import implements, TracError
from trac.web.api import RequestDone
from trac.web.main import IRequestHandler
from trac.wiki.macros import WikiMacroBase
from trac.util.datefmt import http_date, to_datetime

MY_URL = '/extras/xslt'
tl     = threading.local()

def resolver(URL, ID, ctxt):
    scheme = URL.split(':', 2)[0]
    if scheme not in ['wiki', 'ticket', 'browser', 'file']:
        return None

    auth, path = re.match('[^:]*://([^/]*)/(.*)', URL).group(1, 2)
    obj = XsltMacro._get_src(tl.env, tl.req, scheme, auth.replace('%2F', '/'), path)
    return obj.getStream()

libxml2.setEntityLoader(resolver)


class XsltMacro(WikiMacroBase):
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
     * `url::<url>``			`''(note the double colon)''

    However, the full form is almost never necessary. There are three short forms:
     * `<id>:<file>`, where id may be either a ticket shorthand (`#<num>`),
       '''source''', '''htdocs''', '''http''' or '''https''', or the name of a wiki
       page.
     * `<file>` to refer to a local attachment named 'file'. This only works from
       within that wiki page or a ticket.
     * `<url>` to refer to a url; must be an `http://...` or `https://...` url.

    The remaining arguments are optional:
     * `use_iframe` means generate an <iframe> tag instead of directly rendering
       the result.
     * `use_object` is just like `use_iframe` except that it uses an <object> tag
       instead of an <iframe> tag
     * `if_*` are all passed as attributes to the <iframe> tag with the `if_` prefix stripped
     * `obj_*` are all passed as attributes to the <object> tag with the `obj_` prefix stripped
     * `xp_*` are all passed as parameters to the xsl transformer with the `xp_` prefix
       stripped

    When referencing a file in a repository on Trac 0.12 or later (with
    multi-repository support), the first part of the file is used to select
    the repository - if it doesn't match any repository, then the default
    repository is used.

    Examples:
    {{{
        [[Xslt(style.xsl, data.xml)]]
    }}}
    (both style.xsl and data.xml are attachments on the current page).

    You can use stylesheets and docs from other pages, other tickets, or other modules:
    {{{
        [[Xslt(OtherPage:foo.xsl, BarPage:bar.xml)]]         # attachments on other wiki pages
        [[Xslt(base/sub:bar.xsl, foo.xml)]]                  # hierarchical wiki page
        [[Xslt(view.xsl, #3:baz.xml)]]                       # attachment on ticket #3 is data
        [[Xslt(view.xsl, ticket:36:boo.xml)]]                # attachment on ticket #36 is data
        [[Xslt(view.xsl, source:/trunk/docs/foo.xml)]]       # doc from default repository
        [[Xslt(view.xsl, source:/repo2/trunk/docs/foo.xml)]] # doc from repository 'repo2'
        [[Xslt(htdocs:foo/bar.xsl, data.xml)]]               # stylesheet in project htdocs dir.
        [[Xslt(view.xsl, http://test.foo.bar/bar.xml)]]      # xml in external url (only http(s) urls allowed)
    }}}

    Passing parameters to the transform:
    {{{
        [[Xslt(style.xsl, data.xml, xp_foo="hello")]]       # pass foo="hello" to the transform
    }}}

    ''Adapted from the Image macro that's part of trac''
    """

    implements(IRequestHandler)

    def expand_macro(self, formatter, name, args):
        # parse arguments
        # we expect the 1st and 2nd arguments to be filenames (filespecs)
        args = args.split(',')
        if len(args) < 2:
            raise Exception("Insufficient arguments. Need at least a stylesheet and a doc")

        stylespec = self._parse_filespec(args[0].strip(), formatter.context, self.env)
        docspec   = self._parse_filespec(args[1].strip(), formatter.context, self.env)
        opts      = self._parse_opts(args[2:])

        if 'use_iframe' in opts or 'use_object' in opts:
            params = dict(self._get_opts(opts, 'xp_', False))
            url = self.env.href(MY_URL, ss_mod=stylespec[0], ss_id=stylespec[1],
                                ss_fil=stylespec[2], doc_mod=docspec[0],
                                doc_id=docspec[1], doc_fil=docspec[2], **params)

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
                attrs.update(self._get_opts(opts, 'if_'))

                res += """
                  <iframe src="%(src)s" onload="maximizeFrame(this)" %(attrs)s></iframe>
                  """ % { 'src': url,
                          'attrs': ' '.join([ k + '="' + str(v) + '"' for k,v in attrs.iteritems() ]) }

            if 'use_object' in opts:
                attrs = { 'style': 'width: 100%; margin: 0pt' }
                attrs.update(self._get_opts(opts, 'obj_'))

                res += """
                  <object data="%(src)s" type="text/html" onload="maximizeFrame(this)" %(attrs)s></object>
                  """ % { 'src': url,
                          'attrs': ' '.join([ k + '="' + str(v) + '"' for k,v in attrs.iteritems() ]) }

            return res

        else:
            style_obj = self._get_src(self.env, formatter.req, *stylespec)
            doc_obj   = self._get_src(self.env, formatter.req, *docspec)
            params    = dict(self._get_opts(opts, 'xp_'))

            page, ct  = self._transform(style_obj, doc_obj, params, self.env, formatter.req)

            return page

    def _parse_opts(self, args):
        s_opts = ['use_iframe', 'use_object']       # simple opts (no value)
        v_opts = []                                 # valued opts
        p_opts = ['if_', 'obj_', 'xp_']             # prefixed opts

        opts = {}
        for arg in args:
            parts = arg.strip().split('=', 1)
            name = parts[0].strip()
            if self._has_prefix(name, p_opts):
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

    def _has_prefix(self, name, pfx_list):
        for pfx in pfx_list:
            if name.startswith(pfx): return True

        return False

    def _to_str(self, obj):
        if isinstance(obj, str):
            return obj

        if isinstance(obj, unicode):
            return obj.encode('utf-8')

        return str(obj)

    def _parse_filespec(self, filespec, context, env):
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
            module = context.resource.realm or 'wiki'
            id     = context.resource.id
            file   = filespec
            if module not in ['wiki', 'ticket']:
                raise Exception('Cannot reference local attachment from here')
            if not id:
                raise Exception('unknown context id')

        else:
            raise Exception('No filespec given')

        return module, id, file

    def _transform(self, style_obj, doc_obj, params, env, req):
        import libxslt

        def _parse_xml(obj):
            if obj.isFile():
                return libxml2.parseFile(obj.getFile())
            else:
                return libxml2.readDoc(obj.getStream().read(), obj.getUrl(), None, 0)

        tl.env = env
        tl.req = req

        doc    = None
        style  = None;
        result = None;

        try:
            try:
                doc = _parse_xml(doc_obj)
            except Exception, e:
                self.env.log.exception("Error parsing doc '%s'", doc_obj)
                raise Exception("Error parsing %s: %s" % (doc_obj, e))

            try:
                styledoc = _parse_xml(style_obj)
            except Exception, e:
                self.env.log.exception("Error parsing xsl '%s'", style_obj)
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
            tl.req = None

        return output, ct

    def _get_src(env, req, module, id, file):
        # check permissions first
        if module == 'wiki'    and 'WIKI_VIEW' not in req.perm   or \
           module == 'ticket'  and 'TICKET_VIEW' not in req.perm or \
           module == 'file'    and 'FILE_VIEW' not in req.perm   or \
           module == 'browser' and 'BROWSER_VIEW' not in req.perm:
            raise Exception('Permission denied: %s' % module)

        if module == 'browser':
            return BrowserSource(env, req, file)
        if module == 'file':
            return FileSource(env, id, file)
        if module == 'wiki' or module == 'ticket':
            return AttachmentSource(env, module, id, file)
        if module == 'url':
            return UrlSource(file)

        raise Exception("unsupported module '%s'" % module)

    _get_src = staticmethod(_get_src)

    def _get_opts(self, opts, prefix, strip_prefix=True):
        off = strip_prefix and len(prefix) or 0
        return ((self._to_str(k)[off:], self._to_str(opts[k])) \
                                    for k in opts if k.startswith(prefix))

    # IRequestHandler interface

    def match_request(self, req):
        return req.path_info == MY_URL

    def process_request(self, req):
        stylespec = (req.args.get('ss_mod'), req.args.get('ss_id'), req.args.get('ss_fil'))
        docspec   = (req.args.get('doc_mod'), req.args.get('doc_id'), req.args.get('doc_fil'))
        if None in stylespec or None in docspec:
            self.env.log.error("Missing request parameters: %s", req.args)
            raise TracError('Bad request')

        style_obj = self._get_src(self.env, req, *stylespec)
        doc_obj   = self._get_src(self.env, req, *docspec)
        params    = dict(self._get_opts(req.args, 'xp_'))

        lastmod = max(style_obj.get_last_modified(),
                      doc_obj.get_last_modified())

        req.check_modified(lastmod)
        if not req.get_header('If-None-Match'):
            if http_date(lastmod) == req.get_header('If-Modified-Since'):
                req.send_response(304)
                req.end_headers()
                raise RequestDone
        req.send_header('Last-Modified', http_date(lastmod))

        page, content_type = self._transform(style_obj, doc_obj, params, self.env, req)

        req.send_response(200)
        req.send_header('Content-Type', content_type + ';charset=utf-8')
        req.send_header('Content-Length', len(page))
        req.end_headers()

        if req.method != 'HEAD':
            req.write(page)

        raise RequestDone


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
        return "%s://%s/%s" % (self.module, str(self.id).replace("/", "%2F"), self.file)

    def get_last_modified(self):
        return to_datetime(None)

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
    def __init__(self, env, req, file):
        from trac.versioncontrol import RepositoryManager
        from trac.versioncontrol.web_ui import get_existing_node

        if hasattr(RepositoryManager, 'get_repository_by_path'): # Trac 0.12
            repo, file = RepositoryManager(env).get_repository_by_path(file)[1:3]
        else:
            repo = RepositoryManager(env).get_repository(req.authname)
        obj = get_existing_node(req, repo, file, None)

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
        return to_datetime(os.stat(self.obj).st_mtime)

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
        return to_datetime(os.stat(self.obj.path).st_mtime)

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
        lm = self.obj.info().getdate('Last-modified')
        if lm:
            from datetime import datetime
            from util.datefmt import FixedOffset
            return datetime(lm[0], lm[1], lm[2], lm[3], lm[4], lm[5], 0,
                            FixedOffset(lm[9], 'custom'))
        return to_datetime(None)

    def __str__(self):
        return self.obj.url

