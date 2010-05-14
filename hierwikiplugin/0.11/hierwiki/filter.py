from trac.core import *
from trac.web.api import IRequestFilter
from trac.wiki.api import IWikiPageManipulator
from trac.wiki.model import WikiPage
from trac.wiki.web_ui import WikiModule

__all__ = ['EnforceHierarchyModule']

class EnforceHierarchyModule(Component):
    """This check that all subpaths under a wiki page exist.
    This enforces a hierarchy, and prevents accidental misspellings."""
    
    implements(IWikiPageManipulator)
    
    # IWikiPageManipulator methods
    def prepare_wiki_page(self, *args):
        pass # Not currently called
       
    def validate_wiki_page(self, req, page):
        comps = page.name.split('/')
        del comps[-1] # This is the component we are adding to the hierarchy
        
        check = []
        for comp in comps:
            check.append(comp)
            check_page = WikiPage(self.env, '/'.join(check))
            if not check_page.exists:
                yield ('name', 'Hierarchy component "%s" does not exist'%check_page.name)

