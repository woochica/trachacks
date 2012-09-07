# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Adamansky Anton <anton@adamansky.com>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import implements
from trac.mimeview.api import Mimeview
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
    
    implements(ITemplateProvider)
    
    def expand_macro(self, formatter, name, content):
        add_stylesheet(formatter.req, 'lineno/css/lineno.css')
        
        mt = 'txt'
        match = WikiParser._processor_re.match(content)
        if match:
            mt = match.group(1)
            content = content[match.end(1)+1:]
        
        mimeview = Mimeview(formatter.env)
        mimetype = mimeview.get_mimetype(mt) or mimeview.get_mimetype('txt')        
        return mimeview.render(formatter.context, mimetype,
                               content, annotations=['lineno'])
    
    ### ITemplateProvider
    def get_templates_dirs(self):
        return []
    
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('lineno', resource_filename(__name__, 'htdocs'))]
