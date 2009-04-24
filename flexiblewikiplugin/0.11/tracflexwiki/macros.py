# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Alexey Kinyov <rudy@relishgames.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from genshi.builder import tag
from trac.core import *
from trac.util.html import Markup
from trac.wiki.macros import WikiMacroBase

class TracFlexWikiChildrenMacro(WikiMacroBase):
    """Prints children pages on currently opened page.
    """
    
    revision = "$Rev$"
    
    url = "$URL$"

    def expand_macro(self, formatter, name, content):
        """Prints children pages on currently opened page.
        """
        # parse args
        class_="flex-children"
        if content:
            args = content.split(',')
            for arg in args:
                arg = arg.strip()
                if arg.startswith('class='):
                    class_ = arg.split('=', 1)[1].strip()
        # print output
        node = self.get_start_node(formatter, name)
        if node:
            return tag.ul(self.render_node(node, formatter), class_=class_)
        else:
            return ''
    
    def get_start_node(self, formatter, name):
        return formatter.req.args.get('node')
    
    def render_node(self, node, formatter):
        html = tag.li(tag.a(node.title,href=node.href))
        if node.children and len(node.children):
            html_children = [self.render_node(child, formatter) for child in node.children];
            if node.isroot:
                html += html_children
            else:
                html += tag.ul(html_children)
        return html

class TracFlexWikiTreeMacro(TracFlexWikiChildrenMacro):
    """Prints expanded navigation tree.
    """
    
    def get_start_node(self, formatter, name):
        node = formatter.req.args.get('node')
        if node:
            return node.root