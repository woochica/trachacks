# -*- coding: utf-8 -*-
#
# Copyright © 2013 Graham Miln <graham.miln@miln.eu>
# All rights reserved.
#
# A Trac plugin for converting [ ] and [x] into HTML checkbox form elements.
#
# Author: Graham Miln <graham.miln@miln.eu>
# Contributions: rjollos
# URI: http://miln.eu/open/checkbox
# License: Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported
# License URI: http://creativecommons.org/licenses/by-nc-sa/3.0/
#
import re

from trac.config import Option
from trac.core import implements, Component
from trac.wiki import IWikiSyntaxProvider

class MilnCheckbox(Component):

    implements(IWikiSyntaxProvider)

    optional_class = Option('miln-checkbox', 'class', '',
        doc="Cascading Style Sheet (CSS) class name to apply to HTML checkboxes.")

    optional_type = Option('miln-checkbox', 'type', 'html',
        doc="Type of checkbox to render; either `html` to render an HTML checkbox using the input tag, or `unicode` to render unicode based ballot box characters ☐ and ☑.")

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

        optional_class = ''
        if self.optional_class != '':
            optional_class = ' class="' + self.optional_class + '"'
            
        if self.optional_type == 'html':
            return "<input type=\"checkbox\"%s disabled=\"disabled\"%s />" % (optional_class, checked)
        else:
            return "<span%s>%s</span>" % (optional_class, ballotbox)
