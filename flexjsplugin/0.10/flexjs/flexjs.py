from trac.core import *
from trac.config import Option, Configuration
from trac.web.chrome import add_script
from trac.web.main import IRequestFilter
import os

class FlexJsModule(Component):
    """A flexible JavaScript provider."""
    
    implements(IRequestFilter)
                    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, content_type):
        global_scripts = Configuration.getlist(self.config, 'flexjs', 'global')
        for script in global_scripts:
            add_script(req, 'common/js/flex/'+script)

        ext_scripts = Configuration.getlist(self.config, 'flexjs', 'ext')
        idx = 0
        js = req.hdf.get('chrome.scripts.%i.href' % idx)
        idx = len(js)
        for script in ext_scripts:
            req.hdf['chrome.scripts.%i' % idx] = {'href': script, 'type': 'text/javascript'}
            idx += 1
            
        local_scripts = Configuration.getlist(self.config, 'flexjs', 'local')
        for script in local_scripts:
            add_script(req, 'site/js/'+script)
        
        return (template, content_type)
        