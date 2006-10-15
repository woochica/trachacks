# FilenameSearch plugin
from trac.core import *
from trac.Search import ISearchSource
from trac.perm import IPermissionRequestor

from fnmatch import fnmatchcase

class FilenameSearchModule(Component):
    """Search source for filenames in the repository."""
    
    implements(ISearchSource, IPermissionRequestor)
    
    # ISearchSource methods
    def get_search_filters(self, req):
        if req.perm.has_permission('FILENAME_SEARCH'):
            yield ('filename', 'File Names', False)
            
    def get_search_results(self, req, terms, filters):
        if 'filename' not in filters: return # Early bailout if we aren't active
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        repo = self.env.get_repository(req.authname)
        youngest_rev = repo.get_youngest_rev()        

        cursor.execute("""SELECT changes.rev, changes.path FROM node_change as changes, 
                            (SELECT max(rev) as rev, path FROM node_change GROUP BY path) as maxes 
                        WHERE changes.node_type=%s AND changes.rev=maxes.rev AND 
                              changes.path=maxes.path AND changes.change_type!=%s""", ('F','D'))
                                                                
        all_files = [(r,p) for r,p in cursor if repo.has_node(p, youngest_rev)]
        
        for term in terms:
            for _, path in all_files:
                if fnmatchcase(path, term):
                    yield ('', path, '1', 'Me', '')
        
    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'FILENAME_SEARCH'
