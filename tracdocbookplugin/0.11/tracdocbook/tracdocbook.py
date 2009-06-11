# -*- coding: utf-8 -*-
""" TracDocBook - A trac plugin that renders DocBook code within a wiki page.

This has currently been tested only on trac 0.10.4 and 0.11.
"""

import codecs
import re
import sha
from cStringIO import StringIO
import os
import sys
import libxml2
import libxslt

from genshi.builder import tag

from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.api import IWikiSyntaxProvider
from trac.mimeview.api import IHTMLPreviewRenderer, MIME_MAP
from trac.web import IRequestHandler
from trac.util import escape
from trac.wiki.formatter import wiki_to_oneliner
from trac import mimeview

class TracDocBookPlugin(Component):
    implements(IWikiMacroProvider, IHTMLPreviewRenderer, IWikiSyntaxProvider)

    def __init__(self):
        self.load_config()

    def load_config(self):
        """Load the tracdocbook trac.ini configuration."""

        # defaults
        stylesheet_file = '/usr/share/xml/docbook/stylesheet/nwalsh/xhtml/docbook.xsl'

        if 'tracdocbook' not in self.config.sections():
            pass    # TODO: do something

        self.stylesheet = self.config.get('tracdocbook', 'stylesheet') or stylesheet_file

        #TODO: check correct values.
        return ''

    def show_err(self, msg):
        """Display msg in an error box, using Trac style."""
        buf = StringIO()
        buf.write('<div id="content" class="error"><div class="message"> \n\
                   <strong>TracDocBook macro processor has detected an \n\
                   error. Please fix the problem before continuing. \n\
                   </strong> <pre>%s</pre> \n\
                   </div></div>' % escape(msg))
        self.log.error(msg)
        return buf

    # IWikiSyntaxProvider methods
    def get_wiki_syntax(self):
        def format(formatter, ns, match):
            return self.internal_render(formatter.req,'latex',match.group(0))
        yield (r"\$[^$]+\$", format)

    def get_link_resolvers(self):
        return []

    # IWikiSyntaxProvider methods
    #   stolen from http://trac-hacks.org/ticket/248

    def get_link_resolvers(self):
        return []

    # IWikiMacroProvider methods
    def get_macros(self):
        yield 'docbook'

    def get_macro_description(self, name):
        if name == 'docbook':
            return """
            This plugin allows DocBook syntax in Trac markup.

            Simply use
            {{{
              {{{
              #!docbook
              [DocBook code]
              }}}
            }}}
            for a block of Docbook code.

            """

    def internal_render(self, req, name, content):
        if not name == 'docbook':
            return 'Unknown macro %s' % (name)

        style = libxslt.parseStylesheetDoc(libxml2.parseFile(self.stylesheet))
        doc = libxml2.parseDoc(content)
        result = style.applyStylesheet(doc, None)
        html = style.saveResultToString(result)
        
        style.freeStylesheet()
        doc.freeDoc()
        result.freeDoc()
        return html[html.find('<body>')+6:html.find('</body>')].strip();

    def expand_macro(self, formatter, name, content):
        return self.internal_render(formatter.req, name, content)

    # needed for Trac 0.10.4
    def render_macro(self, req, name, content):
        return self.internal_render(req, name, content)

    # IHTMLPreviewRenderer methods
    def get_quality_ratio(self, mimetype):
        if mimetype in ('application/tracdocbook'):
            return 2
        return 0

    def render(self, req, mimetype, content, filename=None, url=None):
        text = hasattr(content, 'read') and content.read() or content
        return self.internal_render(req, name, text)

