from trac.core import *

from ctxtnavadd.api import ICtxtnavAdder

class WikiRenameCtxtnavModule(Component):
    """"A module for adding a rename link to the wiki's ctxtnav bar."""
    
    implements(ICtxtnavAdder)
    
    # ICtxtnavAdder methods
    def match_ctxtnav_add(self, req):
        perm = req.perm.has_permission('WIKI_RENAME') or req.perm.has_permission('WIKI_ADMIN')
        return req.path_info.startswith('/wiki') and perm
                            
    def get_ctxtnav_adds(self, req):
        page = req.path_info[6:] or 'WikiStart'
        yield req.href.admin('general','wikirename')+'?redirect=1&src_page='+page, 'Rename page'
