"""
MediaWiki-style markup
parse(text) -- returns safe-html from wiki markup
code based off of mediawiki
"""

import re, random, math, locale
from base64 import b64encode, b64decode
from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from parser import parse

class MediaWikiRenderer(Component):
        """
        Renders plain text in MediaWiki format as HTML
        """
        implements(IWikiMacroProvider)

        def get_macros(self):
                """Return a list of provided macros"""
                yield 'mediawiki'

        def get_macro_description(self, name):
                return '''desc'''

        def expand_macro(self, formatter, name, content):
                if name == 'mediawiki':
                        return parse(content)

        # deprecated interface prior trac 0.11
        def render_macro(self, req, name, content):
                return self.expand_macro(None, name, content)
