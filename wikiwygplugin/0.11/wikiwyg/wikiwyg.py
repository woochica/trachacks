# vim: expandtab tabstop=4

from trac.core import *
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from trac.web.api import IRequestFilter

from pkg_resources import resource_filename

class TracWikiwygModule(Component):
    implements(ITemplateProvider, IRequestFilter)
    
    # ITemplateProvider methods
    
    def get_templates_dirs(self):
        return []
    
    def get_htdocs_dirs(self):
        """Provide the static JavaScript files, CSS, etc."""
        yield ('', resource_filename(__name__, 'htdocs'))
    
    
    # IRequestFilter methods
    
    def pre_process_request(self, req, handler):
        """Load Wikiwyg libs on every page.
        
        (We might want to get more selective eventually.)
        """
        for curScript in ['Wikiwyg', 'Toolbar', 'Wysiwyg', 'Wikitext', 'Preview', 'ClientServer']:
            add_script(req, 'wikiwyg/%s.js' % curScript)
        return handler
    
    # for Genshi templates
    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type
