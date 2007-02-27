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
        yield 'wikiwyg', resource_filename(__name__, 'htdocs')
    
    
    # IRequestFilter methods
    
    def pre_process_request(self, req, handler):
        """Load Wikiwyg libs pages that make use of them."""
        def uses_wikiwyg(req):
            """Return whether the page referenced by req can make use of Wikiwyg."""
            return True  # TODO: Replace this with actual intelligence: perhaps all wiki pages, etc.
        
        if uses_wikiwyg(req):
            for curScript in ['Wikiwyg', 'Toolbar', 'Wysiwyg', 'Wikitext', 'Preview', 'Trac']:  # 'ClientServer' (put this back in when you implement async save)
                add_script(req, 'wikiwyg/%s.js' % curScript)
        return handler
    
    # the Genshi template version
    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type
