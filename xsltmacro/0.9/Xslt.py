# -*- coding: utf-8 -*-
"""
Embed the result of an xslt-transform in wiki-formatted text.

The first argument is the stylesheet specification; the second argument is
the xml-document specification. The specifications may reference
attachments or files in three ways:
 * `module:id:file`, where module can be either '''wiki''' or '''ticket''',
   to refer to the attachment named ''file'' of the specified wiki page or
   ticket.
 * `id:file`: same as above, but id is either a ticket shorthand or a Wiki
   page name.
 * `file` to refer to a local attachment named 'file'. This only works from
   within that wiki page or a ticket.

Also, the file specification may refer to repository files, using the
`source:file` syntax.

The remaining arguments are optional:
 * `use_iframe` means generate an <iframe> tag instead of directly rendering
    the result (this script needs to be installed as a plugin for this to work)
 * `if_*` are all passed as attributes to the iframe with the `if_` prefix stripped

Examples:
{{{
    [[Xslt(style.xsl, data.xml)]]
}}}

You can use stylesheets and docs from other pages, other tickets or other modules:
{{{
    [[Xslt(OtherPage:foo.xsl, BarPage:bar.xml)]]        # if current module is wiki
    [[Xslt(base/sub:bar.xsl, foo.xml)]]                 # from hierarchical wiki page
    [[Xslt(view.xsl, #3:baz.xml)]]                      # if in a ticket, point to #3
    [[Xslt(view.xsl, ticket:36:boo.xml)]]
    [[Xslt(htdocs:foo/bar.xsl, data.xml)]]              # stylesheet in project htdocs dir.
}}}

''Adapted from the Image macro that's part of trac''
"""

import os
from random import randint
from trac.core import Component, implements
from trac.web  import IRequestHandler

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
                       doc_mod=docspec[0], doc_id=docspec[1], doc_fil=docspec[2])

        attrs = { 'style': 'width: 100%; margin: 0pt', 'frameborder': '0', 'scrolling': 'no' }
        attrs.update(dict([(k[3:], v) for k, v in opts.iteritems() if k.startswith('if_')]))

        id = "xslt-iframe-" + str(randint(100, 1<<31))

        return """
          <script type="text/javascript">
          function maximizeIframe(obj, id) {
            iframe = document.getElementById(id)
            if (iframe.contentDocument)         // Netscape/Mozilla/Firefox
                docHeight = iframe.contentDocument.body.scrollHeight + 20
            else                                // Exploder
                docHeight = iframe.document.body.scrollHeight
            obj.style.height = docHeight + 'px'
          }
          </script>
          <iframe src="%(src)s" id="%(id)s" onload="maximizeIframe(this, '%(id)s')" %(attrs)s></iframe>
          """ % { 'id': id, 'src': url, 'attrs': ' '.join([ k + '="' + str(v) + '"' for k,v in attrs.iteritems() ]) }

    else:
        page, ct = _transform(_get_path(env, hdf, *stylespec), _get_path(env, hdf, *docspec))
        return page

def _parse_opts(args):
    s_opts = ['use_iframe']     # simple opts (no value)
    v_opts = []                 # valued opts
    p_opts = ['if_']            # prefixed opts

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

def _parse_filespec(filespec, hdf, env):
    # parse filespec argument to get module and id if contained.
    parts = filespec.split(':')
    if len(parts) == 3:                 # module:id:attachment
        if parts[0] in ['wiki', 'ticket']:
            module, id, file = parts
        else:
            raise Exception("%s module can't have attachments" % parts[0])

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
            module = 'htdocs'
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

def _get_path(env, hdf, module, id, file):
    # check permissions first
    if module == 'wiki'    and not hdf.has_key('trac.acl.WIKI_VIEW')   or \
       module == 'ticket'  and not hdf.has_key('trac.acl.TICKET_VIEW') or \
       module == 'htdocs'  and not hdf.has_key('trac.acl.FILE_VIEW')   or \
       module == 'browser' and not hdf.has_key('trac.acl.BROWSER_VIEW'):
        raise Exception('Permission denied: %s' % module)

    path = None
    if module == 'browser':
        from trac.versioncontrol.web_ui import get_existing_node
        repos = env.get_repository(hdf.get('trac.authname'))
        node  = get_existing_node(env, repos, file, None)
        path  = node.get_content()

    elif module == 'htdocs':
        import re
        file = re.sub('[^a-zA-Z0-9._/-]', '', file)     # remove forbidden chars
        file = re.sub('^/+', '', file)                  # make sure it's relative
        file = os.path.normpath(file)                   # resolve ..'s
        if file.startswith('..'):                       # don't allow above doc-root
            raise Exception("illegal path '%s'" % file)
        path = os.path.join(env.get_htdocs_dir(), file)

    elif module == 'wiki' or module == 'ticket':
        from trac.attachment import Attachment
        attachment = Attachment(env, module, id, file)
        path = attachment.path

    else:
        raise Exception("unsupported module '%s'" % module)

    return path

def _transform(stylepath, docpath):
    import libxslt

    styledoc = _parse_xml(stylepath)
    doc      = _parse_xml(docpath)

    style  = libxslt.parseStylesheetDoc(styledoc)
    result = style.applyStylesheet(doc, None)
    str = style.saveResultToString(result)

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

    return str, ct

def _parse_xml(obj):
    import libxml2

    if isinstance(obj, str) or isinstance(obj, unicode):
        return libxml2.parseFile(obj)
    if hasattr(obj, 'read') and callable(obj.read):
        return libxml2.parseDoc(obj.read())

    raise Exception("unsupported object type '%s'" % type(obj))

class XsltProcessor(Component):
    implements(IRequestHandler)

    def match_request(self, req):
        match = re.match('^' + MY_URL +'$', req.path_info)
        if match: return 1

    def process_request(self, req):
        stylespec = (req.args.get('ss_mod'), req.args.get('ss_id'), req.args.get('ss_fil'))
        docspec   = (req.args.get('doc_mod'), req.args.get('doc_id'), req.args.get('doc_fil'))
        if not stylespec[0] or not stylespec[1] or not stylespec[2] or \
           not docspec[0] or not docspec[1] or not docspec[2]:
            raise TracError('Bad request')

        stylepath = _get_path(self.env, req.hdf, *stylespec)
        docpath   = _get_path(self.env, req.hdf, *docspec)

        stat = os.stat(stylepath)
        lastmod = stat.st_mtime
        stat = os.stat(docpath)
        if lastmod < stat.st_mtime:
            lastmod = stat.st_mtime

        req.check_modified(lastmod)

        page, content_type = _transform(stylepath, docpath)

        req.send_response(200)
        req.send_header('Content-Type', content_type + ';charset=utf-8')
        req.send_header('Content-Length', len(page))
        req._send_cookie_headers()
        req.end_headers()

        if req.method != 'HEAD':
            req.write(page)

        raise RequestDone

