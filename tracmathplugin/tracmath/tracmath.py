""" TracMath - A trac plugin that renders latex formulas within a wiki page.

This has currently been tested only on trac 0.11.
"""

import codecs
import re
import sha
from cStringIO import StringIO
import os
import sys

from genshi.builder import tag

from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.mimeview.api import IHTMLPreviewRenderer, MIME_MAP
from trac.web import IRequestHandler
from trac.util import escape
from trac.wiki.formatter import wiki_to_oneliner
from trac import mimeview

__author__ = 'Reza Lotun'
__author_email__ = 'rlotun@gmail.com'

tex_preamble = r"""
\documentclass{article}
\usepackage{amsmath}
\usepackage{amsthm}
\usepackage{amssymb}
\usepackage{bm}
\pagestyle{empty}
\begin{document}
"""

rePNG = re.compile(r'.+png$')
reGARBAGE = [
             re.compile(r'.+aux$'),
             re.compile(r'.+log$'),
             re.compile(r'.+tex$'),
             re.compile(r'.+dvi$'),
            ]

class TracMathPlugin(Component):
    implements(IWikiMacroProvider, IHTMLPreviewRenderer, IRequestHandler)

    def __init__(self):
        self.load_config()

    def load_config(self):
        """Load the tracmath trac.ini configuration."""

        # defaults
        tmp = '/tmp/tracmath'
        latex = '/usr/bin/latex'
        dvipng = '/usr/bin/dvipng'
        max_png = 500

        if 'tracmath' not in self.config.sections():
            pass    # TODO: do something

        self.cacheDirectory = self.config.get('tracmath', 'cache_dir') or tmp
        self.latex_cmd = self.config.get('tracmath', 'latex_cmd') or latex
        self.dvipng_cmd = self.config.get('tracmath', 'dvipng_cmd') or dvipng
        self.max_png = self.config.get('tracmath', 'max_png') or max_png
        self.max_png = int(self.max_png)

        if not os.path.exists(self.cacheDirectory):
            os.mkdir(self.cacheDirectory, 0777)

        #TODO: check correct values.
        return ''

    def show_err(self, msg):
        """Display msg in an error box, using Trac style."""
        buf = StringIO()
        buf.write('<div id="content" class="error"><div class="message"> \n\
                   <strong>TracMath macro processor has detected an \n\
                   error. Please fix the problem before continuing. \n\
                   </strong> <pre>%s</pre> \n\
                   </div></div>' % escape(msg))
        self.log.error(msg)
        return buf

    # IWikiMacroProvider methods
    def get_macros(self):
        yield 'latex'

    def get_macro_description(self, name):
        if name == 'latex':
            return 'LaTeX'

    def internal_render(self, req, name, content):
        if not name == 'latex':
            return 'Unknown macro %s' % (name)

        key = sha.new(content.encode('utf-8')).hexdigest()

        imgname = key + '.png'
        imgpath = os.path.join(self.cacheDirectory, imgname)

        if not os.path.exists(imgpath):

            texname = key + '.tex'
            texpath = os.path.join(self.cacheDirectory, texname)

            try:
                f = codecs.open(texpath, encoding='utf-8', mode='w')
                f.write(tex_preamble)
                f.write(content)
                f.write('\end{document}')
                f.close()
            except Exception, e:
                return self.show_err("Problem creating tex file: %s" % (e))

            os.chdir(self.cacheDirectory)
            cmd = self.latex_cmd + ' %s' % texname
            pin, pout, perr = os.popen3(cmd)
            pin.close()
            out = pout.read()
            err = perr.read()

            if len(err) and len(out):
                return 'Unable to call: %s %s %s' % (cmd, out, err)

            cmd = "".join([self.dvipng_cmd,
                    " -T tight -x 1200 -z 9 -bg Transparent ",
                    "-o %s %s" % (imgname, key + '.dvi')])
            pin, pout, perr = os.popen3(cmd)
            pin.close()
            out = pout.read()
            err = perr.read()

            if len(err) and len(out):
                pass # TODO: check for real errors

            self.manage_cache()

        return '<img src="%s/tracmath/%s" />' % (req.base_url, imgname)

    def manage_cache(self):

        ftime = []

        for name in os.listdir(self.cacheDirectory):

            for ext in reGARBAGE:
                if ext.match(name):
                    os.unlink(os.path.join(self.cacheDirectory, name))

            if rePNG.match(name):
                info = os.stat(os.path.join(self.cacheDirectory, name))
                ftime.append((info[7], name))

        ftime.sort(reverse=True)

        numfiles = len(ftime)
        files = (name for _, name in ftime)

        while numfiles > self.max_png:
            name = files.next()
            os.unlink(os.path.join(self.cacheDirectory, name))
            numfiles -= 1


    def expand_macro(self, formatter, name, content):
        return self.internal_render(formatter.req, name, content)

    # IHTMLPreviewRenderer methods
    def get_quality_ratio(self, mimetype):
        if mimetype in ('application/tracmath'):
            return 2
        return 0

    def render(self, req, mimetype, content, filename=None, url=None):
        text = hasattr(content, 'read') and content.read() or content
        return self.internal_render(req, name, text)

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/tracmath')

    def process_request(self, req):
        pieces = [item for item in req.path_info.split('/tracmath') if item]

        if pieces:
            pieces = [item for item in pieces[0].split('/') if item]
            if pieces:
                name = pieces[0]
                img_path = os.path.join(self.cacheDirectory, name)
                return req.send_file(img_path,
                        mimeview.get_mimetype(img_path))
        return

