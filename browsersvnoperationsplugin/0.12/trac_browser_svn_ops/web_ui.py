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
            
            # Insert link to show upload form
            if data['dir']:
                add_ctxtnav(req, 'Upload file', '#upload')
                
                # Insert upload dialog into div#main
                upload_stream = Chrome(self.env).render_template(req,
                        'file_upload.html', data, fragment=True)
                upload_transf = Transformer('//div[@id="main"]')
                stream |=  upload_transf.append(
                        upload_stream.select('//div[@id="dialog-bsop_upload"]')
                        )
            
            # Insert move/delete form
            if data['dir']:
                data['bsop_base_path'] = req.args.get('path')
                
                mvdel_stream = Chrome(self.env).render_template(req,
                        'move_delete.html', data, fragment=True)
                mvdel_transf = Transformer('//div[@id="main"]')
                stream |= mvdel_transf.append(
                        mvdel_stream.select('//div[@id="bsop_move_delete"]')
                        )
        return stream
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if req.path_info.startswith('/browser') and req.method == 'POST' \
                and 'bsop_upload_file' in req.args:
            self._process_request(req, handler)
        else:
            return handler

    def post_process_request(self, req, template, data, content_type):
        return (template, data, content_type)
    
    # Private methods
    def _process_request(self, req, handler):
        self.log.debug('Handling file upload %s %s',
                       req.authname, req.args)
        filename = req.args.get('bsop_upload_file').filename
        file_data = req.args.get('bsop_upload_file').value # or .file for fo
        commit_msg = req.args.get('bsop_upload_commit')
        self.log.debug('Received file %s with %i bytes', 
                       filename, len(file_data))
        repos_path = '/'.join([req.args.get('path'), filename])
        
        repos = RepositoryManager(self.env).get_repository(None)
        
        try:
            repos_path = repos.normalize_path(repos_path)
            self.log.debug('Writing file %s to %s in %s', 
                           filename, repos_path, repos)
            svn_writer = SubversionWriter(repos)
            rev = svn_writer.put_content(repos_path, file_data, filename,
                                         commit_msg)
        finally:
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
