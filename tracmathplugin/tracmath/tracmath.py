import re
import sha
from cStringIO import StringIO
import os
import sys
import tempfile

from genshi.builder import tag

from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.mimeview.api import IHTMLPreviewRenderer, MIME_MAP
from trac.web import IRequestHandler
from trac.util import escape
from trac.wiki.formatter import wiki_to_oneliner
from trac import mimeview

__author__ = 'Reza Lotun'

tex_preamble = r"""
\documentclass{article}
\usepackage{amsmath}
\usepackage{amsthm}
\usepackage{amssymb}
\usepackage{bm}
\pagestyle{empty}
\begin{document}
"""

cacheDirectory = '/tmp'

class TracMathPlugin(Component):
    implements(IWikiMacroProvider, IHTMLPreviewRenderer, IRequestHandler)


    # IWikiMacroProvider methods
    def get_macros(self):
        yield 'latex'

    def get_macro_description(self, name):
        if name == 'latex':
            return 'LaTeX'

    # WANT TO USE THIS!
    #def expand_macro(formatter, name, content):
    #    """ Called by formatter when rendering the parsed wiki text """
    #    pass

    def render_macro(self, req, name, content):
        if not name == 'latex':
            return 'Unknown macro %s' % (name)

        key = sha.new(content).hexdigest()
        imgname = key + '.png'
        imgpath = os.path.join(cacheDirectory, imgname)

        if not os.path.exists(imgpath):
            fd, texfn = tempfile.mkstemp(suffix='.tex', prefix='tracmath')

            f = os.fdopen(fd, 'w+')

            f.write(tex_preamble)
            f.write(content)
            f.write('\end{document}')

            f.close()

            os.chdir(cacheDirectory)
            cmd = '/usr/bin/latex %s' % texfn
            pin, pout, perr = os.popen3(cmd)
            pin.close()
            out = pout.read()
            err = perr.read()

            if len(err) and len(out):
                return 'Unable to call: %s %s %s' % (cmd, out, err)

            tex_base = os.path.basename(texfn.replace('.tex', ''))
            tex_path = os.path.dirname(texfn)

            cmd = "/usr/bin/dvipng -T tight -x 1200 -z 9 -bg Transparent " \
                    + "-o %s %s" % (imgname, tex_base)
            pin, pout, perr = os.popen3(cmd)
            pin.close()
            out = pout.read()
            err = perr.read()

        #if len(err) and len(out):
        #    return 'Unable to call: %s %s %s' % (cmd, out, err)

        return '<img src="%s/tracmath/%s" />' % (req.base_url, imgname)
        
    # IHTMLPreviewRenderer methods
    def get_quality_ratio(self, mimetype):
        if mimetype in ('application/tracmath'):
            return 2
        return 0

    def render(self, req, mimetype, content, filename=None, url=None):
        text = hasattr(content, 'read') and content.read() or content
        return self.render_macro(req, name, text)

    # IRequestHandler methods
    def match_request(self, req):
        #return re.match(r'/tracmath(?:_trac)?(?:/.*)?$', req.path_info)
        return req.path_info.startswith('/tracmath')

    def process_request(self, req):
        pieces = [item for item in req.path_info.split('/tracmath') if item]

        if pieces:
            pieces = [item for item in pieces[0].split('/') if item]
            if pieces:
                name = pieces[0]
                img_path = os.path.join(cacheDirectory, name)
                return req.send_file(img_path,
                        mimeview.get_mimetype(img_path))
        return

