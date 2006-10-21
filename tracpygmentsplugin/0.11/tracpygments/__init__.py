# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Matthew Good <matt@matt-good.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
#
# Author: Matthew Good <matt@matt-good.net>

"""Syntax highlighting module, based on the Pygments module.
"""

import re
from StringIO import StringIO

from trac.core import *
from trac.config import ListOption
from trac.mimeview.api import IHTMLPreviewRenderer, Mimeview
from trac.wiki.api import IWikiMacroProvider

__all__ = ['PygmentsRenderer', 'PygmentsProcessors']

types = {
    'text/x-python':            ('python', 9),
    'text/x-ruby':              ('ruby', 9),
    'text/x-perl':              ('perl', 9),
    'text/x-lua':               ('lua', 9),
    'text/x-chdr':              ('c', 9),
    'text/x-csrc':              ('c', 9),
    'text/x-c++hdr':            ('cpp', 9),
    'text/x-c++src':            ('cpp', 9),
    'text/x-pascal':            ('pascal', 9),
    'text/x-java':              ('java', 9),
    'text/x-vba':               ('vbnet', 9),
    'application/x-javascript': ('javascript', 9), # FIXME application/ or text/
    'text/css':                 ('css', 9),
    'text/html':                ('html', 9),
    'application/xhtml+xml':    ('html', 9),
    'text/x-php':               ('php', 9),
    'application/x-httpd-php':  ('php', 9),
    'application/x-httpd-php3': ('php3', 9),
    'application/x-httpd-php4': ('php4', 9),
    'application/x-httpd-php5': ('php5', 9),
    'application/xml':          ('xml', 9),
    'text/x-sql':               ('sql', 9),
    'text/x-makefile':          ('make', 9),
    'text/x-diff':              ('diff', 9),
    'image/svg+xml':            ('xml', 9)

# TODO 'application/rss+xml':      ('HyperText', 3, {'asp.default.language':1}),

# TODO
# csharp *.cs
# boo *.boo
# brainfuck *.bf, *.b
# ini *.ini *.cfg
# irc
# tex *.tex, *.aux, *.toc
}

class PygmentsRenderer(Component):
    """Syntax highlighting based on Pygments."""

    implements(IHTMLPreviewRenderer)

    enscript_modes = ListOption('mimeviewer', 'pygments_modes',
        '', doc=
        """List of additional MIME types known by Pygments.
        For each, a tuple `mimetype:mode:quality` has to be
        specified, where `mimetype` is the MIME type,
        `mode` is the corresponding Pygments mode to be used
        for the conversion and `quality` is the quality ratio
        associated to this conversion.
        That can also be used to override the default
        quality ratio used by the Pygments render.""")

    expand_tabs = True

    def __init__(self):
        self._types = None

    def get_quality_ratio(self, mimetype):
        # Extend default MIME type to mode mappings with configured ones
        if not self._types:
            self._types = {}
            self._types.update(types)
            self._types.update(
                Mimeview(self.env).configured_modes_mapping('pygments'))
        return self._types.get(mimetype, (None, 0))[1]

    def render(self, req, mimetype, content, filename=None, rev=None):
        try:
            mimetype = mimetype.split(';', 1)[0]
            lang = self._types[mimetype][0]
            return _format(lang, content, True)
        except (KeyError, ValueError):
            raise Exception("No Pygments lexer found for mime-type '%s'."
                            % mimetype)


def _format(lang, content, annotate=False):
    import pygments
    lexer = pygments.get_lexer_by_name(lang)
    formatter = pygments.get_formatter_by_name('html', noclasses=True,
                    cssclass = not annotate and 'code' or '')
    html = pygments.highlight(content, lexer, formatter).rstrip('\n')
    if annotate:
        return html[len('<div><pre>'):-len('</pre></div>')].splitlines()
    else:
        return html


class PygmentsProcessors(Component):
    implements(IWikiMacroProvider)

    def __init__(self):
        self.languages = {}
        try:
            from pygments.lexers._mapping import LEXERS
            for pkg, name, aliases, filetypes in LEXERS.itervalues():
                for alias in aliases:
                    self.languages[alias] = name
        except ImportError:
            pass

    def get_macros(self):
        return self.languages.keys()

    def get_macro_description(self, name):
        return 'Syntax highlighting for %s using Pygments' % self.languages[name]

    def render_macro(self, req, name, content):
        return _format(name, content)
