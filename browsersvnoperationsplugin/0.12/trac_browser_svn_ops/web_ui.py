from pkg_resources import resource_filename
from trac.core import *
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, \
                            add_meta, add_script, add_stylesheet, add_ctxtnav, \
                            Chrome

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
            add_script(req, 'trac_browser_svn_ops/js/jquery-ui.js') # TODO Add jquery-ui conditionally
            add_script(req, 'trac_browser_svn_ops/js/trac-browser-ops.js')
            
        return stream
