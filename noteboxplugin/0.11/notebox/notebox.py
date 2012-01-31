# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Bernhard Gruenewaldt <trac@gruenewaldt.net>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re
from pkg_resources import resource_filename
from genshi.builder import tag
from trac.core import implements
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.api import parse_args
from trac.wiki.formatter import format_to_html
from trac.wiki.macros import WikiMacroBase

class NoteBox(WikiMacroBase):
    """
    The !NoteBox macro will render a small colored box with an
    icon and text. 
    
    To display a !NoteBox on a page, you must call the !NoteBox
    macro and pass the ''style'' and ''text'' as arguments. The
    text may contain wiki formatting, however it is not possible
    to embed other wiki macros within the macro. Also, commas must
    be escaped with a backslash.
    
    A third optional argument allows the ''width'' of the !NoteBox
    to be specified. The ''width'' can be specified in pixels
    as a percent of the page width. The default width is 70%.
    
    The following styles are available: '''warn''', '''tip'''
    and '''note'''.
    
    Examples:
    {{{
    [[NoteBox(warn,If you don't run `update` before `commit`\, your checkin may fail.)]]
    [[NoteBox(tip,The !NoteBox macro can bring '''attention''' to text within a page.,50%)]]
    [[NoteBox(note,More styles may be added in a ''future'' release.,350px)]]
    }}}
    
    [[NoteBox(warn,If you don't run `update` before `commit`\, your checkin may fail.)]]
    [[NoteBox(tip,The !NoteBox macro can bring '''attention''' to text within a page.,50%)]]
    [[NoteBox(note,More styles may be added in a ''future'' release.,350px)]]
    """    
    
    implements(ITemplateProvider)

    def expand_macro(self, formatter, name, content):
        add_stylesheet(formatter.req, 'notebox/css/notebox.css')
        args, kwargs = parse_args(content)
        width = len(args) > 2 and args[2] or '70%'
        div = tag.div(format_to_html(self.env, formatter.context, args[1]), 
                      class_='notebox-%s' % (args[0],),
                      style='width: %s' % (width,))
        return div

    # ITemplateProvider
    def get_htdocs_dirs(self):
        return [('notebox', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
