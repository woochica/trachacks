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
        #youngest_rev = repo.get_youngest_rev()        

        cursor.execute("""SELECT max("""+db.cast('rev','int')+"""), path FROM node_change
                          WHERE node_type = %s AND change_type != 'D'
                          GROUP BY path""", ('F',))

        all_files = [(r,p) for r,p in cursor]# if repo.has_node(p, youngest_rev)]
        cset_cache = {}
        
        for term in terms:
            for rev, path in all_files:
                if fnmatchcase(path, term):
                    cset = cset_cache.setdefault(rev, repo.get_changeset(rev))
                    yield (req.href.browser(path, rev=rev), path, cset.date, cset.author, '')
        
    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'FILENAME_SEARCH'
