import os
import unicodedata

from pkg_resources import resource_filename
from trac.core import *
from trac.config import BoolOption, IntOption
from trac.perm import IPermissionRequestor
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.web.chrome import ITemplateProvider, \
                            add_meta, add_script, add_stylesheet, add_ctxtnav, \
                            Chrome, tag
from trac.versioncontrol.api import RepositoryManager

from genshi.filters.transform import Transformer

from contextmenu.contextmenu import ISourceBrowserContextMenuProvider

from trac_browser_svn_ops.svn_fs import SubversionWriter

class TracBrowserOps(Component):
    implements(ITemplateProvider, ITemplateStreamFilter, IRequestFilter,
               IPermissionRequestor)
    
    include_jqueryui = BoolOption('browserops', 'include_jqueryui', True,
        '''Include a copy of jQuery UI when extending TracBrowser page.
        
        The plugin uses and includes jQuery UI, but this might already be 
        included by other means. Set False to have this plugin use a provided
        copy of jQuery UI and not it's own.''')
    
    max_upload_size = IntOption('browserops', 'max_upload_size', 262144,
        '''Maximum allowed file size (in bytes) for file uploads. Set to 0 for
        unlimited upload size.''')
    
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        '''Return directories from which to serve js, css and other static files
        '''
        return [('trac_browser_svn_ops', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        '''Return directories from which to fetch templates for rendering
        '''
        return [resource_filename(__name__, 'templates')]
    
    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['REPOSITORY_MODIFY', 
                ('REPOSITORY_ADMIN', ['REPOSITORY_MODIFY']),
                ]
        
    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'browser.html' \
                and req.perm.has_permission('REPOSITORY_MODIFY'):
            self.log.debug('Extending TracBrowser')
            
            if self.include_jqueryui:
                add_stylesheet(req, 
                        'trac_browser_svn_ops/css/smoothness/jquery-ui.css')
                add_script(req, 'trac_browser_svn_ops/js/jquery-ui.js') 
            
            add_stylesheet(req, 
                           'trac_browser_svn_ops/css/trac_browser_ops.css')
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
            req.perm.require('REPOSITORY_MODIFY')
            
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
        
        # Retrieve uploaded file
        upload_file = req.args['bsop_upload_file']
        
        # Retrieve filename, normalize, use to check a file was uploaded
        # Filename checks adapted from trac/attachment.py
        filename = getattr(upload_file, 'filename', '')
        filename = unicodedata.normalize('NFC', unicode(filename, 'utf-8'))
        filename = filename.replace('\\', '/').replace(':', '/')
        filename = os.path.basename(filename)
        if not filename:
            raise TracError('No file uploaded')
        
        # Check size of uploaded file, accepting 0 to max_upload_size bytes
        file_data = upload_file.value # Alternatively .file for file object
        file_size = len(file_data)
        if self.max_upload_size > 0 and file_size > self.max_upload_size:
            raise TracError('Uploaded file is too large, '
                            'maximum upload size: %i' % self.max_upload_size)
        
        self.log.debug('Received file %s with %i bytes', 
                       filename, file_size)
        
        commit_msg = req.args.get('bsop_upload_commit')
        
        self.log.debug('Opening repository for file upload')
        reponame, repos, path = self._get_repository(req)
        try:
            repos_path = repos.normalize_path('/'.join([path, filename]))
            self.log.debug('Writing file %s to %s in %s', 
                           filename, repos_path, reponame)
            svn_writer = SubversionWriter(repos, req.authname)
            
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
            svn_writer = SubversionWriter(repos, req.authname)
            
            if operation == 'delete':
                self.log.info('Deleting %s in repository %s',
                              src_path, reponame)
                svn_writer.delete([src_path], commit_msg)
            
            elif operation == 'move':
                self.log.info('Moving %s to %s in repository %s',
                              src_path, dst_path, reponame)
                svn_writer.move([src_path], dst_path, commit_msg)
                
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
            svn_writer = SubversionWriter(repos, req.authname)

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
        if req.perm.has_permission('REPOSITORY_MODIFY'):
            return tag.a('Delete %s' % (entry.name), href='#', 
                         class_='bsop_delete')
        else:
            return None

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
        if req.perm.has_permission('REPOSITORY_MODIFY'):
            return tag.a('Move %s' % (entry.name), href='#',
                         class_='bsop_move')
        else:
            return None

class SvnEditMenu(Component):
    '''Generate context menu items for moving subversion items
    '''
    implements(ISourceBrowserContextMenuProvider)
    
    # IContextMenuProvider methods
    def get_order(self, req):
        return 7

    def get_draw_separator(self, req):
        return True
    
    def get_content(self, req, entry, stream, data):
        if req.perm.has_permission('REPOSITORY_MODIFY') \
                and entry.kind == 'file':
            reponame = data['reponame'] or ''
            filename = os.path.join(reponame, entry.path)
            return tag.a('Edit %s' % (entry.name), 
                         href=req.href.browser(filename, action='edit'),
                         class_='bsop_edit')
        else:
            return None

class TracBrowserEdit(Component):
    implements(ITemplateProvider, ITemplateStreamFilter, IRequestFilter,
               IPermissionRequestor)
    
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        '''Return directories from which to serve js, css and other static files
        '''
        return [('trac_browser_svn_ops', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        '''Return directories from which to fetch templates for rendering
        '''
        return [resource_filename(__name__, 'templates')]

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['REPOSITORY_MODIFY', 
                ('REPOSITORY_ADMIN', ['REPOSITORY_MODIFY']),
                ]
        
    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        return stream
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        return (template, data, content_type)
