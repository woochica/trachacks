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

from genshi.core import Markup

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
    '<>': '&ne;', # '!=' can't be used, because of the '!' escaping
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
    '(TM)': '&trade;',
    '...': '&hellip;',
    }


class Symbols(Component):

    implements(IWikiSyntaxProvider, IWikiMacroProvider)

    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        yield ("!?" + prepare_regexp(SYMBOLS), self._format_symbol)

    def get_link_resolvers(self):
        return []

    def _format_symbol(self, formatter, match, fullmatch):
        return Markup(SYMBOLS[match])

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'ShowSymbols'

    def get_macro_description(self, name):
        return ("Renders in a table the list of known symbols. "
                "Optional argument is the number of columns in the table "
                "(defaults 3).")

    def render_macro(self, req, name, content):
        return render_table(SYMBOLS.keys(), content,
                            lambda s: self._format_symbol(req, s, None))
