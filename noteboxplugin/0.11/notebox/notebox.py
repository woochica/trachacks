# -*- coding: utf-8 -*-
"""
= !NoteBox: The HintBox for Trac =

This macro renders a colored div box.

== Installation ==

See http://trac-hacks.org/wiki/NoteBoxPlugin

== Usage ==

To display the notebox on a page, you must call the !NoteBox
macro on that page an pass the textcontent as
argument.

== Additional information and a life example ==

Please visit: http://trac-hacks.org/wiki/NoteBoxPlugin

== Author and License ==

 * Copyright 2008, Bernhard Gruenewaldt (trac at gruenewaldt.net)

{{{
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
}}}

"""
import re
from inspect import getdoc, getmodule
from pkg_resources import resource_filename
from genshi.builder import tag
from trac.core import Component, implements
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.api import IWikiMacroProvider, parse_args
from trac.wiki.formatter import format_to_html

class NoteBox(Component):
    implements(IWikiMacroProvider, ITemplateProvider, IRequestFilter)

    # IWikiMacroProvider
    def get_macros(self):
        yield 'NoteBox'

    def expand_macro(self, formatter, name, content):
        args, kwargs = parse_args(content)
        div = tag.div(format_to_html(self.env, formatter.context, args[1]), 
                      class_='notebox-%s' % (args[0],))
        return div       

    def get_macro_description(self, name):        
        return getdoc(getmodule(self))

    # ITemplateProvider
    def get_htdocs_dirs(self):
        return [('notebox', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IRequestFilter
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        add_stylesheet(req, 'notebox/css/notebox.css')
        return (template, data, content_type)

