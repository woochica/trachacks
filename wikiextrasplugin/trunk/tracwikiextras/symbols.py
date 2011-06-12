# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2011 Mikael Relbe <mikael@relbe.se>
# All rights reserved.
#
# Copyright (C) 2006 Christian Boos <cboos@neuf.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# Author: Christian Boos <cboos@neuf.fr>
#         Mikael Relbe <mikael@relbe.se>

from genshi.core import Markup

from trac.config import BoolOption, ConfigSection, ListOption
from trac.core import implements, Component
from trac.wiki import IWikiSyntaxProvider, IWikiMacroProvider

from tracwikiextras.util import prepare_regexp, render_table


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
    """Replace character sequences with symbols.

    Characters and symbols are configurable in the `[wikiextras-symbols]`
    section in `trac.ini`. Use the `ShowSymbols` macro to display a list of
    currently defined symbols.
    """
    
    implements(IWikiMacroProvider, IWikiSyntaxProvider)

    symbols_section = ConfigSection('wikiextras-symbols',
            """The set of symbols is configurable by providing associations
            between symbols and wiki keywords. A default set of symbols and
            keywords is defined, which can be revoked one-by-one (_remove) or
            all at once (_remove_defaults).

            Example:
            {{{
            [wikiextras-symbols]
            _remove_defaults = true
            _remove = <- ->
            &laquo; = <<
            &raquo; = >>
            &sum; = (SUM)
            &hearts; = <3
            }}}

            Keywords are space-separated!

            A symbol can also be removed by associating it with no keyword:
            {{{
            &larr; =
            }}}

            Use the `ShowSymbols` macro to find out the current set of symbols
            and keywords.
            """)

    remove_defaults = BoolOption('wikiextras-symbols', '_remove_defaults',
                                 False, doc="Set to true to remove all "
                                            "default symbols.")

    remove = ListOption('wikiextras-symbols', '_remove', sep=' ', doc="""\
            Space-separated(!) list of keywords that shall not be interpreted
            as symbols (even if defined in this section).""")

    def __init__(self):
        self.symbols = None

    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        if self.symbols is None:
            self.symbols = SYMBOLS.copy()
            if self.remove_defaults:
                self.symbols = {}
            for symbol, value in self.symbols_section.options():
                if not symbol.startswith('_remove'):
                    if value:
                        for keyword in value.split():
                            self.symbols[keyword.strip()] = symbol
                    else:
                        # no keyword, remove all keywords associated with
                        # symbol
                        for k in self.symbols.keys():
                            if self.symbols[k] == symbol:
                               del self.symbols[k]
            for keyword in self.remove:
                if keyword in self.symbols:
                    del self.symbols[keyword]

        if self.symbols:
            yield ("!?" + prepare_regexp(self.symbols), self._format_symbol)
        else:
            yield (None, None)

    def get_link_resolvers(self):
        return []

    #noinspection PyUnusedLocal
    def _format_symbol(self, formatter, match, fullmatch):
        return Markup(self.symbols[match])

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'ShowSymbols'

    #noinspection PyUnusedLocal
    def get_macro_description(self, name):
        return ("Renders in a table the list of known symbols. "
                "Optional argument is the number of columns in the table "
                "(defaults 3).")

    #noinspection PyUnusedLocal
    def expand_macro(self, formatter, name, content, args=None):
        return render_table(self.symbols.keys(), content,
                            lambda s: self._format_symbol(formatter, s, None),
                            colspace=4)
