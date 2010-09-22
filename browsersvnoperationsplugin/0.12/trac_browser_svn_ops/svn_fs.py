import urllib

from trac.core import Component, implements, Interface, TracError
from trac.versioncontrol import Changeset, Node, Repository, \
                                IRepositoryConnector, \
                                NoSuchChangeset, NoSuchNode
from trac.versioncontrol.svn_fs import SubversionRepository, SubversionNode      
from trac.versioncontrol.cache import CachedRepository

class SubversionWriter(object):
    def __init__(self, repos, username):
        self.repos = repos
        self.log = repos.log
        self.username = username
        
    def put_content(self, repos_path, content, filename, commit_msg):
        from svn import core, fs, repos
        
        log=self.log
        
        svn_repos = self._get_libsvn_handle()
                
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

    def delete(self, repos_paths, commit_msg):
        from svn import core, fs, repos
        
        log = self.log
        svn_repos = self._get_libsvn_handle()
        repos_paths_utf8 = [rp.encode('utf-8') for rp in repos_paths]
        commit_msg_utf8 = commit_msg.encode('utf-8')
        username_utf8 = self.username.encode('utf-8')
        rev = self.repos.get_youngest_rev()
        
        pool = core.Pool()
        
        log.debug('btfc')
        fs_txn = repos.fs_begin_txn_for_commit(svn_repos, rev, username_utf8,
                                               commit_msg_utf8, pool)
        log.debug('tr')
        fs_root = fs.txn_root(fs_txn, pool)
            
        log.debug('cp')
        for repos_path_utf8 in repos_paths_utf8:
            kind = fs.check_path(fs_root, repos_path_utf8, pool)
        
            if kind == core.svn_node_none:
                raise TracError('Delete', repos_path)
        
        for repos_path_utf8 in repos_paths_utf8:
            fs.delete(fs_root, repos_path_utf8)
         
        log.debug('ct')                                     
        new_rev = repos.fs_commit_txn(svn_repos, fs_txn, pool)
    
    def make_dir(self, repos_path, commit_msg):
        from svn import core, fs, repos
        
        log = self.log
        svn_repos = self._get_libsvn_handle()
        repos_path_utf8 = repos_path.encode('utf-8')
        commit_msg_utf8 = commit_msg.encode('utf-8')
        username_utf8 = self.username.encode('utf-8')
        rev = self.repos.get_youngest_rev()
        
        pool = core.Pool()
        
        log.debug('btfc')
        fs_txn = repos.fs_begin_txn_for_commit(svn_repos, rev, username_utf8,
                                               commit_msg_utf8, pool)
        log.debug('tr')
        fs_root = fs.txn_root(fs_txn, pool)
            
        log.debug('cp')
        kind = fs.check_path(fs_root, repos_path_utf8, pool)
        
        if kind != core.svn_node_none:
            raise TracError('Make directory: %s already exists' % repos_path)
        else:
            fs.make_dir(fs_root, repos_path_utf8)
         
        log.debug('ct')                                     
        new_rev = repos.fs_commit_txn(svn_repos, fs_txn, pool)
        
    def move(self, src_paths, dst_path, commit_msg):
        from svn import core, client, repos, fs
        
        def _log_message(item, pool):
            return commit_msg_utf8
                
        src_urls = [self._path_to_url(src_path) for src_path in src_paths]
        dst_url = self._path_to_url(dst_path)
        
        src_urls_utf8 = [src_url.encode('utf-8') for src_url in src_urls]
        dst_url_utf8 = dst_url.encode('utf-8')
        dst_path_utf8 = dst_path.encode('utf-8')
        commit_msg_utf8 = commit_msg.encode('utf-8')
        username_utf8 = self.username.encode('utf-8')
        
        # Open a transaction and check whether dst_path exists and if it's a
        # directory. Abort the transaction since no changes are made.
        svn_repos = self._get_libsvn_handle()
        rev = self.repos.get_youngest_rev()
        fs_ptr = repos.fs(svn_repos)
        fs_txn = fs.begin_txn(fs_ptr, rev)
        txn_root = fs.txn_root(fs_txn)
        kind = fs.check_path(txn_root, dst_path_utf8)
        fs.abort_txn(fs_txn)
        
        # Abort if destination is unsuitable
        if kind not in (core.svn_node_none, core.svn_node_dir):
            raise TracError('Cannot move "%s" to "%s", destination exists '
                            'and is not a directory.' % (src_path, dst_path))
        
        # Prepare a subversion context to supply the commit message
        client_ctx = client.create_context()
        client_ctx.log_msg_func3 = client.svn_swig_py_get_commit_log_func
        client_ctx.log_msg_baton3 = _log_message
        
        # Add subversion authentication baton to the client context
        # Since we're dealing with file:// urls authentication is not used
        # but subversion will not function without it
        auth_providers = [
                client.svn_client_get_simple_provider(),
                client.svn_client_get_username_provider(),
                ]
        client_ctx.auth_baton = core.svn_auth_open(auth_providers)
        
        # Set the username supplied, otherwise owner of subversion proces would
        # be logged
        core.svn_auth_set_parameter(client_ctx.auth_baton,
                core.SVN_AUTH_PARAM_DEFAULT_USERNAME, username_utf8)
        
        # Move files and dirs from from src to dst. 
        # Don't force
        # Place src files/dirs in in dst if dst exists, 
        # Don't create parents of dst.
        # Don't set additional revision properties
        commit_info = client.svn_client_move5(tuple(src_urls_utf8),
                                              dst_url_utf8,
                                              False, 
                                              True, 
                                              False,
                                              None, 
                                              client_ctx)
        return commit_info.revision
    
    def _get_repos_direct_object(self):
        '''Retrieve the uncached, direct repository object.
        '''
        if isinstance(self.repos, SubversionRepository):
            repos = self.repos
        elif isinstance(self.repos, CachedRepository):
            repos = self.repos.repos
        else:
            raise TracError('Repository type %s is not supported by %s' 
                            % (type(self.repos), 'TracBrowserSvnOpsPlugin'))
        return repos
        
    def _get_libsvn_handle(self):
        '''Retrieve the libsvn repository handle from the Trac object.
        '''
        return self._get_repos_direct_object().repos

    def _path_to_url(self, path):
        '''Encode a path in the repos as a fully qualified URL.
        '''
        repos = self._get_repos_direct_object()
        url_parts =  ['file:///', 
                      urllib.quote(repos.path.lstrip('/')),
                      '/',
                      urllib.quote(path.lstrip('/')),
                      ]
        return ''.join(url_parts)
