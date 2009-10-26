""" Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
    $Id$
    $HeadURL$

    This is Free Software under the BSD license.

    The regexes XML_NAME (unchanged) and NUM_HEADLINE (added 'n'-prefix for all
    names) were taken from trac.wiki.parser and the base code of method
    `_parse_heading` was taken from trac.wiki.formatter which are:
        Copyright (C) 2003-2008 Edgewall Software
        All rights reserved.
    See http://trac.edgewall.org/wiki/TracLicense for details.

"""
from trac.core import *
from trac.wiki.api import IWikiSyntaxProvider

__url__      = r"$URL$"[6:-2]
__author__   = r"$Author$"[9:-2]
__revision__ = int(r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]


class DashesSyntaxPlugin(Component):
    """ Trac Plug-in to provide Wiki Syntax for em and en dashes.
    """
    implements(IWikiSyntaxProvider)

    RE_DASH  = r"(?P<endash>(?<!-)-{2,3}(?!-))"
    HTML_EN_DASH = "&#8211;"
    HTML_EM_DASH = "&#8212;"

    def _dash(self, formatter, match, fullmatch):
        if match == '--':
            return self.HTML_EN_DASH
        elif match == '---':
            return self.HTML_EM_DASH
        else:
            return match

    def get_wiki_syntax(self):
        yield  ( self.RE_DASH , self._dash )

    def get_link_resolvers(self):
        return []

