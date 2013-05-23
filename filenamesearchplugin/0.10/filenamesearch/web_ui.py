# FilenameSearch plugin
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.config import BoolOption

try:
    from trac.search import ISearchSource  # 0.11
except ImportError:
    from trac.Search import ISearchSource  # 0.10

from fnmatch import fnmatchcase

class FilenameSearchModule(Component):
    """Search source for filenames in the repository."""

    check_gone = BoolOption('filenamesearch', 'check_gone', default=True,
                            doc='Check if files are present in the youngest rev before returning.')    
    show_gone = BoolOption('filenamesearch', 'show_gone', default=True,
                           doc='Show files that are in the DB, but not in the youngest rev. (These may indicate moved files)')
    
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
        # ???: Ask cboos about this. <NPK>
        if isinstance(youngest_rev, basestring) and youngest_rev.isdigit():
            youngest_rev = int(youngest_rev)        

        cursor.execute("""SELECT max("""+db.cast('rev','int')+"""), path FROM node_change
                          WHERE node_type = %s AND change_type != 'D'
                          GROUP BY path""", ('F',))

        all_files = [(r,p) for r,p in cursor]# if repo.has_node(p, youngest_rev)]
        cset_cache = {}
        
        for term in terms:
            for rev, path in all_files:
                match = None
                if '/' in term:
                    match = fnmatchcase(path, term.lstrip('/'))
                else:
                    match = sum([fnmatchcase(x, term) for x in path.split('/')])
                if match:
                    cset = cset_cache.setdefault(rev, repo.get_changeset(rev))
                    msg = ''
                    if self.check_gone and not repo.has_node(path, youngest_rev):
                        if self.show_gone:
                            msg = 'Not in the youngest revision, file has possibly been moved.'
                        else:
                            continue
                    yield (req.href.browser(path, rev=rev), path, cset.date, cset.author, msg)
        
    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'FILENAME_SEARCH'
