from pkg_resources import resource_filename
from trac.core import *
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.web.chrome import ITemplateProvider, \
                            add_meta, add_script, add_stylesheet, add_ctxtnav, \
                            Chrome, tag
from trac.versioncontrol.api import RepositoryManager

from genshi.filters.transform import Transformer

from contextmenu.contextmenu import ISourceBrowserContextMenuProvider

from trac_browser_svn_ops.svn_fs import SubversionWriter

class TracBrowserOps(Component):
    implements(ITemplateProvider, ITemplateStreamFilter, IRequestFilter)
    
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        '''Return directories from which to serve js, css and other static files
        '''
        return [('trac_browser_svn_ops', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        '''Return directories from which to fetch templates for rendering
        '''
        return [resource_filename(__name__, 'templates')]
    
    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'browser.html':
            self.log.debug('Extending TracBrowser')
            
            add_stylesheet(req, 
                           'trac_browser_svn_ops/css/smoothness/jquery-ui.css')
            add_stylesheet(req, 
                           'trac_browser_svn_ops/css/trac_browser_ops.css')
            
            # TODO Add jquery-ui conditionally
            add_script(req, 'trac_browser_svn_ops/js/jquery-ui.js') 
            add_script(req, 'trac_browser_svn_ops/js/trac_browser_ops.js')
            
            # Insert browser operations elements when directory/file shown
            if data['dir']:
                # Insert upload dialog and move/delete dialog into div#main
                bsops_stream = Chrome(self.env).render_template(req,
                        'trac_browser_ops.html', data, fragment=True)
                bsops_transf = Transformer('//div[@id="main"]')
                stream |=  bsops_transf.append(
                        bsops_stream.select('//div[@class="bsop_dialog"]')
                        )
                
                # Insert button bar after file/directory table
                bsops_stream = Chrome(self.env).render_template(req,
                        'trac_browser_ops.html', data, fragment=True)
                bsops_transf = Transformer('//table[@id="dirlist"]')
                stream |=  bsops_transf.after(
                        bsops_stream.select('//div[@id="bsop_buttons"]')
                        )
                
        return stream
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if req.path_info.startswith('/browser') and req.method == 'POST':
            self.log.debug('Intercepting browser POST')
            
            # Dispatch to private handlers based on which form submitted
            # The handlers perform a redirect, so don't return the handler
            if 'bsop_upload_file' in req.args:
                self._upload_request(req, handler)
            
            elif 'bsop_mvdel_op' in req.args:
                self._move_delete_request(req, handler)
            
            elif 'bsop_create_folder_name' in req.args:
                self._create_path_request(req, handler)
        else:
            return handler

    def post_process_request(self, req, template, data, content_type):
        return (template, data, content_type)
    
    # Private methods
    
    def _get_repository(self, req):
        '''From req identify and return (reponame, repository, path), removing 
        reponame from path in the process.
        '''
        path = req.args.get('path')
        repo_mgr = RepositoryManager(self.env)
        reponame, repos, path = repo_mgr.get_repository_by_path(path)
        return reponame, repos, path
        
    def _upload_request(self, req, handler):
        self.log.debug('Handling file upload for "%s"', req.authname)
        
        # Retrieve uploaded fields
        filename = req.args.get('bsop_upload_file').filename
        file_data = req.args.get('bsop_upload_file').value # or .file for fo
        commit_msg = req.args.get('bsop_upload_commit')
        self.log.debug('Received file %s with %i bytes', 
                       filename, len(file_data))
        
        self.log.debug('Opening repository for file upload')
        reponame, repos, path = self._get_repository(req)
        try:
            repos_path = repos.normalize_path('/'.join([path, filename]))
            self.log.debug('Writing file %s to %s in %s', 
                           filename, repos_path, repos)
            svn_writer = SubversionWriter(repos)
            rev = svn_writer.put_content(repos_path, file_data, filename,
                                         commit_msg)
        finally:
            repos.sync()
            self.log.debug('Closing repository')
            repos.close()
        
        # Perform http redirect back to this page in order to rerender
        # template according to new repository state
        req.redirect(req.href(req.path_info))

    def _move_delete_request(self, req, handler):
        self.log.debug('Handling move/delete for %s',
                       req.authname)
        operation = req.args.get('bsop_mvdel_op') #Moving or deleting?
        src_name = req.args.get('bsop_mvdel_src_name') # Item to move or delete
        dst_name = req.args.get('bsop_mvdel_dst_name') # Destination if move
        commit_msg = req.args.get('bsop_mvdel_commit')
        
        self.log.debug('Opening repository for %s', operation)
        reponame, repos, path = self._get_repository(req)
        try:
            src_path = repos.normalize_path('/'.join([path, src_name]))
            dst_path = repos.normalize_path('/'.join([path, dst_name]))
            svn_writer = SubversionWriter(repos)
            
            if operation == 'delete':
                self.log.info('Deleting %s in repository %s',
                              src_path, reponame)
                svn_writer.delete(repos_path, commit_msg)
            
            elif operation == 'move':
                self.log.info('Moving %s to %s in repository %s',
                              src_path, dst_path, reponame)
                svn_writer.move(src_path, dst_path, commit_msg)
                
        finally:
            repos.sync()
            self.log.debug('Closing repository')
            repos.close()
        
        # Perform http redirect back to this page in order to rerender
        # template according to new repository state
        req.redirect(req.href(req.path_info))
    
    def _create_path_request(self, req, handler):
        self.log.debug('Handling create folder for %s',
                       req.authname)
                       
        create_name = req.args.get('bsop_create_folder_name')
        commit_msg = req.args.get('bsop_create_commit')
        
        self.log.debug('Opening repository to create folder')
        reponame, repos, path = self._get_repository(req)
        try:
            create_path = repos.normalize_path('/'.join([path, create_name]))
            svn_writer = SubversionWriter(repos)

            self.log.info('Creating folder %s in repository %s',
                          create_path, reponame)
            svn_writer.make_dir(create_path, commit_msg)
        
        finally:
            repos.sync()
            self.log.debug('Closing repository')
            repos.close()
        
        # Perform http redirect back to this page in order to rerender
        # template according to new repository state
        req.redirect(req.href(req.path_info))


class SvnDeleteMenu(Component):
    '''Generate context menu items for deleting subversion items
    '''
    implements(ISourceBrowserContextMenuProvider)
    
    # IContextMenuProvider methods
    def get_order(self, req):
        return 5

    def get_draw_separator(self, req):
        return True
    
    def get_content(self, req, entry, stream, data):
        return tag.a('Delete %s' % (entry.name), href='#', 
                     class_='bsop_delete')

class SvnMoveMenu(Component):
    '''Generate context menu items for moving subversion items
    '''
    implements(ISourceBrowserContextMenuProvider)
    
    # IContextMenuProvider methods
    def get_order(self, req):
        return 6

    def get_draw_separator(self, req):
        return True
    
    def get_content(self, req, entry, stream, data):
        return tag.a('Move %s' % (entry.name), href='#',
                     class_='bsop_move')
