# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Adamansky Anton <anton@adamansky.com>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.builder import tag
from trac.core import *
from trac.mimeview.api import Mimeview
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.macros import WikiMacroBase

import inspect
import re

_processor_re = re.compile('#\!([\w+-][\w+-/]*)')

class LinenoMacro(WikiMacroBase):
    """Wiki processor that prints line-numbered code listings"""
    
    implements(ITemplateProvider)
    
    # ITemplateProvider
    def get_templates_dirs(self):
        return []
    
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('lineno', resource_filename(__name__, 'htdocs'))]
    
    def expand_macro(self, formatter, name, content):
        add_stylesheet(formatter.req, 'lineno/css/lineno.css')
        mt = 'txt'
        match = _processor_re.search(content)
        if match:
            mt = match.group().strip()[2:]
            content = content[match.end():]
        
        mimetype = Mimeview(formatter.env).get_mimetype(mt)
        if not mimetype:
            mimetype = Mimeview(formatter.env).get_mimetype('txt')
        
        annotations = ['lineno']
        return Mimeview(self.env).render(formatter.context,
                                         mimetype, content,
                                         None, None, annotations)
