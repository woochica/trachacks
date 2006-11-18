from trac.core import *
from trac.web.api import IRequestFilter
from trac.config import ListOption

try:
    set = set
except ImportError:
    from sets import Set as set

__all__ = ['NavHiderModule']

class NavHiderModule(Component):
    """Request filter to hide entries in navigation bars."""

    mainnav = ListOption('navhider', 'mainnav',
                              doc='Items to remove from the mainnav bar')

    metanav = ListOption('navhider', 'metanav',
                              doc='Items to remove from the metanav bar')
                             
    implements(IRequestFilter)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, content_type):
        self._remove_items(req, 'mainnav')
        self._remove_items(req, 'metanav')    
        return template, content_type

    # Internal methods
    def _remove_items(self, req, name):
        items = set(getattr(self, name))
        for item in self.config.get('trac', name, default='').split(','):
            item = item.strip()
            if item[0] == '-' or item[0] == '!':
                items.add(item[1:])
        for item in items:
            req.hdf.removeTree('chrome.nav.%s.%s'%(name,item))
        
