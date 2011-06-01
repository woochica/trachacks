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

# See http://www.w3.org/TR/html401/sgml/entities.html for the official list
# and http://www.cookwood.com/html/extras/entities.html for an illustration.

from genshi.core import Markup

from trac.core import implements, Component
from trac.wiki import IWikiSyntaxProvider, IWikiMacroProvider

from goodies.util import *


ENTITIES = [
    "nbsp", "iexcl", "cent", "pound", "curren", "yen", "brvbar", "sect",
    "uml", "copy", "ordf", "laquo", "not", "shy", "reg", "macr", "deg",
    "plusmn", "sup2", "sup3", "acute", "micro", "para", "middot", "cedil",
    "sup1", "ordm", "raquo", "frac14", "frac12", "frac34", "iquest",
    "Agrave", "Aacute", "Acirc", "Atilde", "Auml", "Aring", "AElig",
    "Ccedil", "Egrave", "Eacute", "Ecirc", "Euml", "Igrave", "Iacute",
    "Icirc", "Iuml", "ETH", "Ntilde", "Ograve", "Oacute", "Ocirc", "Otilde",
    "Ouml", "times", "Oslash", "Ugrave", "Uacute", "Ucirc", "Uuml", "Yacute",
    "THORN", "szlig", "agrave", "aacute", "acirc", "atilde", "auml", "aring",
    "aelig", "ccedil", "egrave", "eacute", "ecirc", "euml", "igrave", "iacute",
    "icirc", "iuml", "eth", "ntilde", "ograve", "oacute", "ocirc", "otilde",
    "ouml", "divide", "oslash", "ugrave", "uacute", "ucirc", "uuml", "yacute",
    "thorn", "yuml", "fnof", "Alpha", "Beta", "Gamma", "Delta", "Epsilon",
    "Zeta", "Eta", "Theta", "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi",
    "Omicron", "Pi", "Rho", "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi",
    "Omega", "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta",
    "theta", "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi",
    "rho", "sigmaf", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega",
    "thetasym", "upsih", "piv", "bull", "hellip", "prime", "Prime", "oline",
    "frasl", "weierp", "image", "real", "trade", "alefsym", "larr", "uarr",
    "rarr", "darr", "harr", "crarr", "lArr", "uArr", "rArr", "dArr", "hArr",
    "forall", "part", "exist", "empty", "nabla", "isin", "notin", "ni",
    "prod", "sum", "minus", "lowast", "radic", "prop", "infin", "ang", "and",
    "or", "cap", "cup", "int", "there4", "sim", "cong", "asymp", "ne",
    "equiv", "le", "ge", "sub", "sup", "nsub", "sube", "supe", "oplus",
    "otimes", "perp", "sdot", "lceil", "rceil", "lfloor", "rfloor", "lang",
    "rang", "loz", "spades", "clubs", "hearts", "diams", "quot", "amp", "lt",
    "gt", "OElig", "oelig", "Scaron", "scaron", "Yuml", "circ", "tilde",
    "ensp", "emsp", "thinsp", "zwnj", "zwj", "lrm", "rlm", "ndash", "mdash",
    "lsquo", "rsquo", "sbquo", "ldquo", "rdquo", "bdquo",
    "dagger", "Dagger", "permil", "lsaquo", "rsaquo", "euro"
    ]


class Entities(Component):

    implements(IWikiSyntaxProvider, IWikiMacroProvider)

    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        yield (r"!?&#\d+;", self._format_entity)
        yield (r"!?&(?:%s);" % '|'.join(ENTITIES), self._format_entity)

    def get_link_resolvers(self):
        return []

    def _format_entity(self, formatter, match, fullmatch):
        return Markup(match)

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'ShowEntities'

    def get_macro_description(self, name):
        return ("Renders in a table the list of HTML entities. "
                " Optional argument is the number of columns in the table "
                "(defaults 3).")

    def render_macro(self, req, name, content):
        return render_table(["&%s;" % e for e in ENTITIES], content,
                            lambda e: Markup(' ' + e)) # see #G429

