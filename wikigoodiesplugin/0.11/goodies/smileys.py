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

# See also http://moinmoin.wikiwikiweb.de/HelpOnSmileys

import re

from genshi.builder import tag

from pkg_resources import resource_filename

from trac.core import implements, Component
from trac.web.chrome import ITemplateProvider
from trac.wiki import IWikiSyntaxProvider, IWikiMacroProvider

from goodies.util import *


SMILEYS = {
    ":)": "smile.png",
    ":-)": "smile.png",
    "B-)": "smile2.png",
    "B)": "smile2.png",
    ":))": "smile3.png",
    ":-))": "smile3.png",
    ";-)": "smile4.png",
    ":D": "biggrin.png",
    ";)": "smile4.png",
    ":(": "sad.png",
    ":-(": "sad.png",
    ":-?": "tongue.png",
    ":o": "redface.png",
    "<:(": "frown.png",
    "|)": "tired.png",
    ':\\': "ohwell.png",
    ">:>": "devil.png",
    "X-(": "angry.png",
    "|-)": "tired.png",

    "(./)": "checkmark.png",
    "(!)": "idea.png",
    "<!>": "attention.png",
    '/!\\': "alert.png",
    "{p1}": "prio1.png",
    "{p2}": "prio2.png",
    "{p3}": "prio3.png",
    "{P1}": "prio1.png",
    "{P2}": "prio2.png",
    "{P3}": "prio3.png",
    "{o}": "star_off.png",
    "{*}": "star_on.png",
    "{OK}": "thumbs-up.png",
    "{!OK}": "thumbs-dn.png",
    "{UP}": "thumbs-up.png",
    "{DN}": "thumbs-dn.png",
    "(y)": "thumbs-up.png",
    "{X}": "icon-error.png",
}


class Smileys(Component):

    implements(IWikiSyntaxProvider, IWikiMacroProvider, ITemplateProvider)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return [('smileys', resource_filename(__name__, 'htdocs/modern/img'))]
                
    def get_templates_dirs(self):
        return []
    
    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        yield (r"(?<!\w)!?(?:%s)" % prepare_regexp(SMILEYS),
               self._format_smiley)

    def get_link_resolvers(self):
        return []

    def _format_smiley(self, formatter, match, fullmatch):
        return tag.img(src=formatter.href.chrome('smileys', SMILEYS[match]),
                       alt=match, style="vertical-align: bottom")

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'ShowSmileys'

    def get_macro_description(self, name):
        return ("Renders in a table the list of available smileys. "
                "Optional argument is the number of columns in the table "
                "(defaults 3).")

    def expand_macro(self, formatter, name, content):
        return render_table(SMILEYS.keys(), content,
                            lambda s: self._format_smiley(formatter, s, None))

