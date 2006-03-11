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
    "{1}": "prio1.png",
    "{2}": "prio2.png",
    "{3}": "prio3.png",
    "{o}": "star_off.png",
    "{*}": "star_on.png",
    "{OK}": "thumbs-up.png",
    "{X}": "icon-error.png",
}


class Smileys(Component):

    implements(IWikiSyntaxProvider, IWikiMacroProvider, ITemplateProvider)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        print resource_filename(__name__, 'htdocs')
        return [('smileys', resource_filename(__name__, 'htdocs/modern'))]
                
    def get_templates_dirs(self):
        return []
    
    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        yield (prepare_regexp(SMILEYS), lambda x, y, z: self._format_smiley(y))

    def get_link_resolvers(self):
        return []

    def _format_smiley(self, s):
        return '<img src="%s" alt="%s" style="vertical-align: bottom" />' % \
               (self.env.href.chrome('smileys/img', SMILEYS[s]), s)

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'ShowSmileys'

    def get_macro_description(self, name):
        return ("Renders in a table the list of available smileys. "
                "Optional argument is the number of columns in the table "
                "(defaults 3).")

    def render_macro(self, req, name, content):
        return render_table(SMILEYS.keys(), content, self._format_smiley)

