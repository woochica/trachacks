from trac.core import *
from trac.web.main import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.prefs.api import IPreferencePanelProvider
from trac.config import IntOption

class DropbearFilter(Component):
    """A filter to show dropbears."""
    
    default_dropbears = IntOption('dropbears', 'default', default=0,
                                  doc='The number of dropbears to show by default.')
    
    implements(IRequestFilter, IRequestHandler, ITemplateProvider, IPreferencePanelProvider)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if int(req.session.get('dropbears', self.default_dropbears)):
            add_stylesheet(req, 'dropbear/dropbears.css')
            add_script(req, '/dropbear/dropbears.js')
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type
        
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/dropbear')
        
    def process_request(self, req):
        data = {}
        data['dropbears'] = int(req.session.get('dropbears', self.default_dropbears))
        return 'dropbears.js', data, 'text/plain'
        
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('dropbear', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
        
    # IPreferencePanelProvider methods
    def get_preference_panels(self, req):
        yield 'dropbears', 'Dropbears'
        
    def render_preference_panel(self, req, panel):
        if req.method == 'POST':
            req.session['dropbears'] = req.args.get('dropbears', '')
            req.redirect(req.href.prefs(panel))
        
        data = {}
        data['dropbears'] = int(req.session.get('dropbears', self.default_dropbears))
        return 'prefs_dropbears.html', data