# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Bernhard Gruenewaldt <trac@gruenewaldt.net>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
"""
The !NoteBox macro will render a small colored box with an
icon and text. 

To display a !NoteBox on a page, you must call the !NoteBox
macro and pass the style and text as arguments. The text may
contain wiki formatting, however it is not possible to embed
other wiki macros within the macro. Also, commas must be
escaped with a backslash.

Examples:
{{{
[[NoteBox(warn,If you don't run `update` before `commit`\, your checkin may fail.)]]
[[NoteBox(tip,The !NoteBox macro can bring '''attention''' to text within a page.)]]
[[NoteBox(note,More styles may be added in a ''future'' release.)]]
}}}

[[NoteBox(warn,If you don't run `update` before `commit`\, your checkin may fail.)]]
[[NoteBox(tip,The !NoteBox macro can bring '''attention''' to text within a page.)]]
[[NoteBox(note,More styles may be added in a ''future'' release.)]]
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

