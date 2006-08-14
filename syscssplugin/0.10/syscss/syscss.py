from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
import os

try:
    import syscss_file
    user_file = syscss_file.file
except ImportError:
    user_file = '/usr/share/trac/templates/sys_css.css'

class SysCssPlugin(Component):
    """A system-wide CSS provider."""
    
    implements(INavigationContributor, ITemplateProvider)
    
    def __init__(self):
        self.css = self.config.get('trac','syscss',default=None)
        if not self.css:
            self.css = user_file
        self.css = self.css.strip()
        
    # INavigationContributor methods
    def get_navigation_items(self, req):
        add_stylesheet(req, 'syscss/'+os.path.basename(self.css))
        return []
    
    # ITemplateProvider methods
    def get_templates_dirs(self):
        return []
        
    def get_htdocs_dirs(self):
        return [('syscss',os.path.dirname(self.css))]
