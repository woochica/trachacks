# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2006 Christian Boos <cboos@neuf.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# Author: Christian Boos <cboos@neuf.fr>

import re

from trac.core import implements, Component
from trac.wiki import IWikiSyntaxProvider, IWikiMacroProvider

from goodies.util import *


SYMBOLS = {
    '<-': '&larr;',
    '->': '&rarr;',
    '<->': '&harr;',
    '<=': '&lArr;',
    '=>': '&rArr;',
    '<=>': '&hArr;',
    '>=': '&ge;',
    '=<': '&le;', # ... as <= is already used for &lArr;
    '<>': '&ne;', # != won't work, because of the generic '!' negation
    '--': '&mdash;',
    '(c)': '&copy;',
    '(C)': '&copy;',
    '(R)': '&reg;',
    '1/2': '&frac12;',
    '1/4': '&frac14;',
    '3/4': '&frac34;',
    '+/-': '&plusmn;',
    '/\\': '&and;',
    '\\/': '&or;',
    }

TEXT_SYMBOLS = {
    'TM': '&trade;',
    }

class Symbols(Component):

    implements(IWikiSyntaxProvider, IWikiMacroProvider)

    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        yield (r"\B%s\B" % "|".join([re.escape(i) for i in SYMBOLS]),
               lambda x, y, z: self._format_symbol(y))
        yield (r"\b%s\b" % "|".join([re.escape(i) for i in TEXT_SYMBOLS]),
               lambda x, y, z: self._format_text_symbol(y))

    def get_link_resolvers(self):
        return []

    def _format_symbol(self, i):
        return SYMBOLS[i]

    def _format_text_symbol(self, i):
        return TEXT_SYMBOLS[i]

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'ShowSymbols'

    def get_macro_description(name):
        return """Renders in a table the list of known symbols.

        Optional argument is the number of columns in the table (defaults 3).
        """

    def render_macro(self, req, name, content):
        def render_symbol(s):
            if SYMBOLS.has_key(s):
                return self._format_symbol(s)
            else:
                return self._format_text_symbol(s)
        return render_table(SYMBOLS.keys() + TEXT_SYMBOLS.keys(),
                            content, render_symbol)
