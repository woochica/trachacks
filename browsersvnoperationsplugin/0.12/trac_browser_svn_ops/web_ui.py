from pkg_resources import resource_filename
from trac.core import *
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, \
                            add_meta, add_script, add_stylesheet, add_ctxtnav, \
                            Chrome, tag
from genshi.filters.transform import Transformer

class TracBrowserOps(Component):
    implements(ITemplateProvider, ITemplateStreamFilter)
    
    def get_htdocs_dirs(self):
        '''Return directories from which to serve js, css and other static files
        '''
        return [('trac_browser_svn_ops', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        '''Return directories from which to fetch templates for rendering
        '''
        return [resource_filename(__name__, 'templates')]
    
    def filter_stream(self, req, method, filename, stream, formdata):
        if filename == 'browser.html':
            self.log.debug('Extending TracBrowser')
            
            add_stylesheet(req, 'trac_browser_svn_ops/css/trac_browser_ops.css')
            
            # TODO Add jquery-ui conditionally
            add_script(req, 'trac_browser_svn_ops/js/jquery-ui.js') 
            add_script(req, 'trac_browser_svn_ops/js/trac_browser_ops.js')
            
            add_ctxtnav(req, 'Upload file', '#upload')
            
            # Insert upload dialog into div#main
            upload_stream = Chrome(self.env).render_template(req,
                    'file_upload.html', formdata, fragment=True)
            upload_transf = Transformer('//div[@id="main"]')
            stream = stream | upload_transf.append(upload_stream.select('//div[@id="dialog-bsop_upload"]'))
            
            # Add a radio button to each row of the file/folder list, in the name column
#            transf = Transformer('//table[@id="dirlist"]//td[@class="name"]')
#            stream = stream | transf.append(tag.span(tag.input(type_='radio', name='name', class_='name'), style='text-align:right;'))

        return stream
