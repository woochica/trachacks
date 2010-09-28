import os
import unicodedata

from pkg_resources import resource_filename
from trac.core import *
from trac.config import BoolOption, IntOption
from trac.perm import IPermissionRequestor
from trac.util import pretty_size
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.web.chrome import ITemplateProvider, add_warning, add_notice, \
                            add_meta, add_script, add_stylesheet, add_ctxtnav, \
                            Chrome, tag
from trac.versioncontrol.api import RepositoryManager

from genshi.filters.transform import Transformer

from contextmenu.contextmenu import ISourceBrowserContextMenuProvider

from trac_browser_svn_ops.svn_fs import SubversionWriter, SubversionException

def _get_repository(env, req):
    '''From env and req identify and return (reponame, repository, path), 
    removing reponame from path in the process.
    '''
    path = req.args.get('path')
    repo_mgr = RepositoryManager(env)
    reponame, repos, path = repo_mgr.get_repository_by_path(path)
    return reponame, repos, path


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
                data['max_upload_size'] = self.max_upload_size
                
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
        # TODO Ugly set of conditions, make the if beautiful
        if req.path_info.startswith('/browser') and req.method == 'POST' \
                and ('bsop_upload_file' in req.args
                     or 'bsop_mvdel_op' in req.args
                     or 'bsop_create_folder_name' in req.args):
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
                            'maximum upload size: %s' 
                            % pretty_size(self.max_upload_size))
        
        self.log.debug('Received file %s with %i bytes', 
                       filename, file_size)
        
        commit_msg = req.args.get('bsop_upload_commit')
        
        self.log.debug('Opening repository for file upload')
        reponame, repos, path = _get_repository(self.env, req)
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
        src_names = req.args.getlist('bsop_mvdel_src_name') # Items to move/del
        dst_name = req.args.get('bsop_mvdel_dst_name') # Destination if move
        commit_msg = req.args.get('bsop_mvdel_commit')
        
        # ContextMenuPlugin provides each src as [reponame/][page_path/]node_path
        # The Trac request path is of the form   /[reponame/][page_path]
        # Retrieve just the portion of the src items that is relative to this
        # page by stripping the request path. Do this before the request path 
        # is itself stripped of reponame when retrieving the repository
        path = req.args.get('path')
        src_names = [('/' + src_name).split(path, 1)[1] 
                     for src_name in src_names]
        
        self.log.debug('Opening repository for %s', operation)
        reponame, repos, path = _get_repository(self.env, req)
        try:
            src_paths = [repos.normalize_path('/'.join([path, src_name]))
                         for src_name in src_names]
            dst_path = repos.normalize_path('/'.join([path, dst_name]))
            svn_writer = SubversionWriter(repos, req.authname)
            
            try:
                if operation == 'delete':
                    self.log.info('Deleting %i items in repository %s',
                                  len(src_paths), reponame)
                    svn_writer.delete(src_paths, commit_msg)
                
                elif operation == 'move':
                    self.log.info('Moving %i items to %s in repository %s',
                                  len(src_paths), repr(dst_path), reponame)
                    svn_writer.move(src_paths, dst_path, commit_msg)
                else:
                    raise TracError("Unknown operation %s" % operation)
                    
            except SubversionException, e:
                self.log.exception("Failed when attempting svn operation "
                                   "%s: %s",
                                   operation, e)
                add_warning(req, "Failed to perform %s: %s" 
                             % (operation, 
                                "See the log file for more information"))
            
            add_notice(req, "Performed %s operation" % operation)    

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
        reponame, repos, path = _get_repository(self.env, req)
        try:
            create_path = repos.normalize_path('/'.join([path, create_name]))
            svn_writer = SubversionWriter(repos, req.authname)

            try:
                self.log.info('Creating folder %s in repository %s',
                              create_path, reponame)
                svn_writer.make_dir(create_path, commit_msg)
            
            except SubversionException, e:
                self.log.exception("Failed to create directory: %s", e)
            
                add_warning(req, "Failed to create folder: %s" 
                                 % ("See the log file for more information",))
            
            add_notice(req, "Folder created.")
            
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
        max_edit_size = self.config.getint('browserops', 'max_edit_size')
        if req.perm.has_permission('REPOSITORY_MODIFY') \
                and entry.kind == 'file' \
                and (max_edit_size <= 0 
                     or entry.content_length <= max_edit_size):
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
    
    max_edit_size = IntOption('browserops', 'max_edit_size', 262144,
        '''Maximum allowed file size (in bytes) for edited files. Set to 0 for
        unlimited editting size.''')
        
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
        action = req.args.get('action', '')
        if filename == 'browser.html' and action == 'edit' \
                and req.perm.has_permission('REPOSITORY_MODIFY'):
            # NB TracBrowserOps already inserts javascript and css we need
            # So only add css/javascript needed solely by the editor
            
            if data['file'] and data['file']['preview']['rendered']:
                max_edit_size = self.max_edit_size
                data['max_edit_size'] = max_edit_size
                
                # Discard rendered table, replace with textarea of file contents
                # This means reading the file from the repository again
                # N.B. If a file is rendered as something other than a table
                # e.g. due to PreCodeBrowserPlugin this code won't trigger
                
                # Retrieve the same node that BrowserModule.process_request() 
                # used to render the preview.
                # At this point reponame has been removed from data['path']
                # and repos has already been determined
                repos = data['repos']
                path = data['path']
                rev = data['rev']
                node = repos.get_node(path, rev)
                
                # If node is too large then don't allow editting
                if max_edit_size > 0 and node.content_length > max_edit_size:
                    return stream
                    
                # Read the node and supply it's content to the template data
                data['file_content'] = node.get_content().read()
                
                # Replace the already rendered preview with a form and textarea
                bsops_stream = Chrome(self.env).render_template(req,
                        'file_edit.html', data, fragment=True)
                transf = Transformer('//div[@id="preview"]'
                                     '/table[@class="code"]')
                stream |=  transf.replace(
                        bsops_stream.select('//div[@id="bsop_edit"]'))
        return stream
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if req.path_info.startswith('/browser') and req.method == 'POST' \
                and "bsop_edit_commit" in req.args:
            req.perm.require('REPOSITORY_MODIFY')
            
            self.log.debug('Intercepting browser POST for edit')
            
            # Dispatch to private edit handler method
            # The private handler performs a redirect, so don't return
            if 'bsop_edit_text' in req.args:
                self._edit_request(req, handler)
        else:
            return handler

    def post_process_request(self, req, template, data, content_type):
        return (template, data, content_type)
    
    # Private methods
    def _edit_request(self, req, handler):
        self.log.debug('Handling file edit for "%s"', req.authname)
        
        # Retrieve fields
        # TODO Don't assume encoding of file, detect it beforehand
        text = req.args['bsop_edit_text'].encode('utf-8')
        commit_msg = req.args['bsop_edit_commit_msg']
        max_edit_size = self.max_edit_size
        
        if max_edit_size > 0 and len(text) > max_edit_size:
            raise TracError("The edited texti too long, "
                            "the limit is %s (%i bytes)."
                            % (pretty_size(max_edit_size), max_edit_size))
                             
        self.log.debug('Opening repository for file edit')
        reponame, repos, path = _get_repository(self.env, req)
        try:
            repos_path = repos.normalize_path(path)
            filename = os.path.basename(repos_path)
            self.log.debug('Writing file %s to %s in %s', 
                           filename, repos_path, reponame)
            svn_writer = SubversionWriter(repos, req.authname)
            
            try:
                rev = svn_writer.put_content(repos_path, text, filename,
                                         commit_msg)
                add_notice(req, 'Committed changes to "%s"' % filename)
                
            except SubversionException, e:
                self.log.exception('Failed when attempting svn write: %s',
                                   e)
                add_warning(req, 'Failed to write edited file',
                                 'See the Trac log file for more information')
        finally:
            repos.sync()
            self.log.debug('Closing repository')
            repos.close()
        
        # Perform http redirect back to this page in order to rerender
        # template according to new repository state
        req.redirect(req.href(req.path_info))      
