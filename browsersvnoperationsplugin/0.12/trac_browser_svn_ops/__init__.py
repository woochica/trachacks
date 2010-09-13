from pkg_resources import resource_filename
from trac.core import *
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, \
                            add_meta, add_script, add_stylesheet, add_ctxtnav, \
                            Chrome

class TracBrowserOps(Component):
    implements(ITemplateStreamFilter)
    
    def filter_stream(self, req, method, filename, stream, formdata):
        if filename == 'browser.html':
            self.log.debug('Extending TracBrowser')
            add_meta(req, 'TracBrowserOps just testing')
            add_script(req, 'jquery-ui.js') # TODO Add jquery-ui conditionally
            add_script(req, 'trac-browser-ops.js')
            
        return stream
