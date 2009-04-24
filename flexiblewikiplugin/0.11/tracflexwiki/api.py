# -*- coding: utf-8 -*-

from trac.web.chrome import add_warning
from trac.wiki.api import IWikiChangeListener, IWikiPageManipulator
from trac.wiki.model import WikiPage
from tracflexwiki.core import *
from tracflexwiki.translation import _

class TracFlexWikiSystem(TracFlexWikiComponent):
    """Wiki structure system on top of base wiki system."""
    
    implements(IWikiChangeListener, IWikiPageManipulator)
    
    # IWikiChangeListener methods
    
    def wiki_page_added(self, page):
        pass
    
    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        pass

    def wiki_page_deleted(self, page):
        pass

    def wiki_page_version_deleted(self, page):
        pass
    
    # IWikiPageManipulator methods
    
    def prepare_wiki_page(self, req, page, fields):
        pass

    def validate_wiki_page(self, req, page):
        """ Save 'parent', 'title' to node if changed.
        """
        if ('save' in req.args):
            
            # old & new nodes:
            old = TracFlexWikiNode(self.env, page.name)
            old.fetch()
            node = req.args.get('node')
            
            # check, if new parent exists
            if not (node.parent.isroot or WikiPage(self.env, node.parent.name).exists):
                self._page_not_exists(req)
                return []

            # if new node data is different than old, update it
            if (old.title != node.title) or \
               (old.hidden != node.hidden) or \
               (old.weight != node.weight) or \
               (old.parent.name != node.parent.name):
                # it's a hack - I just want to mark page as changed.
                page.old_text += '\n Hello from TracFlexWikiSystem :)'
                # save
                node.save()
        
        return []
    
    # TracFlexWikiSystem private methods
    
    def _page_not_exists(self, req = None):
        """Raise error when page not found."""
        if req:
            add_warning(req, _('Page or parent page not found.'))
