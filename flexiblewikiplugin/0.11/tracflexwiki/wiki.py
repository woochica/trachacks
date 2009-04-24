# -*- coding: utf-8 -*-
#
# See example: http://trac-hacks.org/browser/tagsplugin/trunk/tractags/wiki.py
#

import re
from genshi.builder import tag
from genshi.filters.transform import Transformer
from genshi.input import HTML
from genshi.template import Context
from trac.core import *
from trac.web.api import ITemplateStreamFilter
from tracflexwiki.core import TracFlexWikiComponent
from tracflexwiki.translation import _

class TracFlexWikiEditFields(TracFlexWikiComponent):
    """Parent field in page edit mode.
    """
    implements(ITemplateStreamFilter)
    
    # ITemplateStreamFilter methods
    
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'wiki_edit.html':
            node=req.args.get('node')
            ctxt = Context(node=node, _ = _)
            # field for 'title'
            title_tpl = self.get_loader().load('wiki_edit_title.html')
            title = title_tpl.generate(ctxt)
            stream = stream | Transformer('//div[@id="rows"]').before(title)
            # field for 'parent'
            parent_tpl = self.get_loader().load('wiki_edit_parent.html')
            parent = parent_tpl.generate(ctxt)
            stream = stream | Transformer('//div[@id="changeinfo1"]').before(parent)            
            # field for 'weight'
            weight_tpl = self.get_loader().load('wiki_edit_weight.html')
            weight = weight_tpl.generate(ctxt)
            stream = stream | Transformer('//div[@id="changeinfo2"]').before(weight)  
            # field for 'hidden'
            hidden_tpl = self.get_loader().load('wiki_edit_hidden.html')
            hidden = hidden_tpl.generate(ctxt)
            stream = stream | Transformer('//div[@id="changeinfo2"]').before(hidden)
        return stream

class TracFlexWikiNavBar(TracFlexWikiComponent):
    """Navigation by structure.
    """
    implements(ITemplateStreamFilter)
    
    # ITemplateStreamFilter methods
    
    def filter_stream(self, req, method, filename, stream, data):
        if self.is_wiki_realm(req):
            navbar_tpl = self.get_loader().load('wiki_navbar.html')
            navbar = navbar_tpl.generate(node=req.args.get('node'), is_not_edit=(not self.is_wiki_edit(req, filename)))
            #stream = stream | Transformer('//p[@class="path"]').remove()
            stream = stream | Transformer('//p[@class="path noprint"]').remove()
            stream = stream | Transformer('//div[@id="content"]').prepend(navbar)
        return stream

