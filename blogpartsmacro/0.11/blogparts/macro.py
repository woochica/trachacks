# -*- coding: utf-8 -*-

from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.util.text import to_unicode,unicode_quote

import model
import os

class Macro(Component):
    implements(IWikiMacroProvider)
    
    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'BlogParts'

    def get_macro_description(self, name): 
        list = model.BlogPart.select(self.env)
        desclist = []
        for blogpart in list:
            desclist.append(blogpart.description )
        return "Provide BlogParts:"+os.linesep.join(desclist)

    def render_macro(self, req, name, content):
        args = content.split(',')
        
        part = model.BlogPart(self.env, args[0])
        if part:
            body = part.body
            argnum = int(part.argnum)
            i = 1
            for arg in args[1:]:
                a = unicode_quote(arg)
                body = body.replace('%'+'arg_%d'%(i)+'%',a)
                i = i+1
            
            return body
        else:
            return 'Not Impremented %s'%args[0]
                