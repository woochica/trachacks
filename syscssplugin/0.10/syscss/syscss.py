from trac.core import *
from trac.config import Option
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_link
from trac.web.main import IRequestFilter
import os

class SysCssModule(Component):
    """A system-wide CSS provider."""
    
    css_path = Option('syscss', 'path', default='/usr/share/trac/sys_css.css',
                      doc='Path to the CSS file')
    path_type = Option('syscss', 'type', default='file',
                       doc='Type of path given. Choices are file and url.')
    
    implements(ITemplateProvider, IRequestFilter)
    
    # INavigationContributor methods
    def get_navigation_items(self, req):
        add_stylesheet(req, 'syscss/'+os.path.basename(self.css))
        return []
        
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, content_type):
        if self.path_type == 'file':
            add_stylesheet(req, 'syscss/'+os.path.basename(self.css_path))
        elif self.path_type == 'url':
            add_link(req, 'stylesheet', self.css_path, mimetype='text/css')
        return (template, content_type)
    
    # ITemplateProvider methods
    def get_templates_dirs(self):
        return []
        
    def get_htdocs_dirs(self):
        if self.path_type == 'file':
            yield ('syscss',os.path.dirname(self.css_path))
