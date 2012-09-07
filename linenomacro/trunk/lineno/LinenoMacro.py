# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Adamansky Anton <anton@adamansky.com>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.builder import tag
from trac.core import implements
from trac.mimeview.api import IHTMLPreviewAnnotator, Mimeview
from trac.util.translation import _
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.macros import WikiMacroBase
from trac.wiki.parser import WikiParser


class LinenoMacro(WikiMacroBase):
    """Wiki processor that prints line numbers for code blocks.
       
       Example:
       
       {{{
       {{{
       #!Lineno
       #!java
       class A {
           public static void main(String[] args) {
           }
       }
       }}}
       }}}
       
       {{{
       #!Lineno
       #!java
       class A {
           public static void main(String[] args) {
           }
       }
       }}}
    """
    
    implements(IHTMLPreviewAnnotator, ITemplateProvider)

    def __init__(self):
        self._anchor = None
    
    def expand_macro(self, formatter, name, content):
        add_stylesheet(formatter.req, 'lineno/css/lineno.css')

        i = 1
        self._anchor = 'a1'
        while self._anchor in formatter._anchors:
            self._anchor = 'a' + str(i)
            i += 1
        formatter._anchors[self._anchor] = True

        mt = 'txt'
        match = WikiParser._processor_re.match(content)
        if match:
            try: #Trac 0.12+
                mt = match.group(2)
                content = content[match.end(2)+1:]
            except IndexError: #Trac 0.11
                mt = match.group(1)
                content = content[match.end(1)+1:]
        
        mimeview = Mimeview(formatter.env)
        mimetype = mimeview.get_mimetype(mt) or mimeview.get_mimetype('txt')        
        return mimeview.render(formatter.context, mimetype,
                               content, annotations=['codeblock-lineno'])


    ### ITemplateProvider methods

    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('lineno', resource_filename(__name__, 'htdocs'))]


    ### ITextAnnotator methods

    # This implementation is almost identical to LineNumberAnnotator
    # in trac.mimeview.api, except we take care to ensure that the id
    # for each line number anchor is unique.

    def get_annotation_type(self):
        return 'codeblock-lineno', _('Line'), _('Line numbers')

    def get_annotation_data(self, context):
        return None

    def annotate_row(self, context, row, lineno, line, data):
        id = self._anchor + '-L%s' % lineno
        row.append(tag.th(id=id)(
            tag.a(lineno, href='#'+id)
        ))
