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

__all__ = ['PygmentsRenderer']

types = {
    'text/x-python':            ('python', 9), # TODO pycon -- console
    'text/x-ruby':              ('ruby', 9), # TODO rbcon/irb -- console
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

# FIXME 'application/rss+xml':      ('HyperText', 3, {'asp.default.language':1}),

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
        import pygments
        try:
            mimetype = mimetype.split(';', 1)[0]
            lang = self._types[mimetype][0]
            lexer = pygments.get_lexer_by_name(lang)
        except (KeyError, ValueError):
            raise Exception("No Pygments lexer found for mime-type '%s'."
                            % mimetype)

        formatter = pygments.get_formatter_by_name('html')
        formatter.cssclass = ''
        formatter.noclasses = True

        html = pygments.highlight(content, lexer, formatter)
        html = html[len('<div><pre>'):-len('</pre></div>\n')]
        return html.splitlines()
