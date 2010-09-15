from trac.core import Component, implements, Interface, TracError
from trac.versioncontrol import Changeset, Node, Repository, \
                                IRepositoryConnector, \
                                NoSuchChangeset, NoSuchNode
from trac.versioncontrol.svn_fs import SubversionRepository, SubversionNode      
from trac.versioncontrol.cache import CachedRepository

class SubversionWriter(object):
    def __init__(self, repos):
        self.repos = repos
        self.log = repos.log
        # TODO Hardcoded username
        self.username = 'alex'
        
    def put_content(self, repos_path, content, filename, commit_msg):
        from svn import core, fs, repos
        
        log=self.log
        
        # TODO Permissions

        # Retrieve the libsvn repository handle from the Trac repository object
        if isinstance(self.repos, SubversionRepository):
            svn_repos = self.repos.repos
        elif isinstance(self.repos, CachedRepository):
            svn_repos = self.repos.repos.repos
        else:
            raise TracError('Repository type %s is not supported' 
                            % type(self.repos))
        log.debug('svn_repos %i type %s', svn_repos, type(svn_repos))
        
        fs_path_utf8 = repos_path.encode('utf-8')
        filename_utf8 = filename.encode('utf-8')
        username_utf8 = self.username.encode('utf-8')
        commit_msg_utf8 = commit_msg.encode('utf-8')
        rev = self.repos.get_youngest_rev()
        log.debug('%s %s', svn_repos, rev)
        
        pool = core.Pool()
                
        log.debug('btfc')
        fs_txn = repos.fs_begin_txn_for_commit(svn_repos, rev, username_utf8,
                                               commit_msg_utf8, pool)
        log.debug('tr')
        fs_root = fs.txn_root(fs_txn, pool)
            
        log.debug('cp')
        kind = fs.check_path(fs_root, fs_path_utf8, pool)
        
        if kind == core.svn_node_none:
            log.debug('mkf')                                       
            fs.make_file(fs_root, fs_path_utf8)
        elif kind == core.svn_node_file:
            pass
        else:
            raise TracError(fs_path_utf8, rev)
        
        log.debug('fat')                                       
        stream = fs.svn_fs_apply_text(fs_root, fs_path_utf8, None, pool)
        log.debug('sw')                                       
        core.svn_stream_write(stream, content)
        log.debug('sc')                                       
        core.svn_stream_close(stream) 
        log.debug('ct')                                       
        new_rev = repos.fs_commit_txn(svn_repos, fs_txn, pool)
        
        return new_rev

