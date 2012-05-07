# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Ryan J Ollos
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.util.datefmt import format_datetime
from trac.wiki.formatter import format_to_oneliner, system_message
from trac.wiki.macros import WikiMacroBase, parse_args
from trac.wiki.model import WikiPage

class WikinfoMacro(WikiMacroBase):
    """
    Output wiki page info.
    
    Currently supported arguments:
    
    author      - Author of first version
    version     - Latest version of page
    changed_by  - Page last changed by
    comment     - Latest comment of changed by
    changed_ts  - Page last changed timestamp
    """
    
    def expand_macro(self, formatter, name, content):
        
        if not content:
            return ''
        
        args, kwargs = parse_args(content)        
        if len(args) > 1:
            return system_message("Number of args can't be greater than 1")
        
        if args[0] == 'author':
            page = WikiPage(self.env, formatter.context.resource, 1)
            text = page.author 
        elif args[0] == 'version':
            page = WikiPage(self.env, formatter.context.resource)
            text = str(page.version)
        elif args[0] == 'changed_by':
            page = WikiPage(self.env, formatter.context.resource)
            text = page.author
        elif args[0] == 'comment':
            page = WikiPage(self.env, formatter.context.resource)
            text = page.comment
        elif args[0] == 'changed_ts':
            page = WikiPage(self.env, formatter.context.resource)
            text = format_datetime(page.time)
        else:
            return system_message("Unkwown argument %s" % args[0])
        
        return format_to_oneliner(self.env, formatter.context, text)
    