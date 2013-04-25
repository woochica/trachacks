# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Graham Miln <graham.miln@miln.eu>
# All rights reserved.
#
# A Trac plugin for converting [ ] and [x] into HTML checkbox form elements.
#
# Author: Graham Miln <graham.miln@miln.eu>
# URI: http://miln.eu/open/checkbox
# License: Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported
# License URI: http://creativecommons.org/licenses/by-nc-sa/3.0/
#
import re

from trac.core import implements, Component
from trac.wiki import IWikiSyntaxProvider

class MilnCheckbox(Component):

    implements(IWikiSyntaxProvider)

    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        yield (
            "\[(?P<contents>[ xX+])\]",
            lambda x, y, z: self._format_checkbox(z.group("contents")))

    def get_link_resolvers(self):
        return []

    def _format_checkbox(self, contents = ' '):
        if contents == ' ':
            ballotbox = u'☐'
            checked = ''
        else:
            ballotbox = u'☑'
            checked = ' checked="checked"'

        optional_class = self.env.config.get('miln_checkbox', 'class', '')
        if optional_class != '':
            optional_class = ' class="'+optional_class+'"'
            
        optional_type = self.env.config.get('miln_checkbox', 'type', 'html')
        if optional_type == 'html':
            return "<input type=\"checkbox\"%s disabled=\"disabled\"%s />" % (optional_class,checked)
        else:
            return "<span%s>%s</span>" % (optional_class,ballotbox)
            
