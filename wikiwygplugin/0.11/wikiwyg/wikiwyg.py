# vim: expandtab tabstop=4
import re

from trac.core import *
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from trac.web.api import IRequestFilter, IRequestHandler

from pkg_resources import resource_filename

class TracWikiwygModule(Component):
    implements(ITemplateProvider, IRequestFilter, IRequestHandler)
    
    # ITemplateProvider methods
    
    def get_templates_dirs(self):
        yield resource_filename(__name__, 'templates')
    
    def get_htdocs_dirs(self):
        """Provide the static JavaScript files, CSS, etc."""
        yield 'wikiwyg', resource_filename(__name__, 'htdocs')
    
    
    # IRequestHandler methods
    
    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        return re.match(r'^/wikiwyg(?:/(.*)|$)', req.path_info) is not None

    def process_request(self, req):
        """For now, just always return Trac.js, as it's the only template we have."""
        return 'Trac.js', {}, 'text/plain'  # TODO: Should be text/javascript, of course, but there's a bug in 0.11 trunk (#4855) that invokes Genshi's XHTML mode for that.
    
    
    # IRequestFilter methods
    
    def pre_process_request(self, req, handler):
        """Load Wikiwyg libs on pages that make use of them."""
        def uses_wikiwyg(req):
            """Return whether the page referenced by req can make use of Wikiwyg."""
            return True  # TODO: Replace this with actual intelligence: perhaps all wiki pages, etc.
        
        if uses_wikiwyg(req):
            for curScript in ['Util', 'Wikiwyg', 'Toolbar', 'Wysiwyg', 'Wikitext', 'Preview']:  # 'ClientServer' (put this back in when you implement async save)
                add_script(req, 'wikiwyg/%s.js' % curScript)
            add_script(req, '/wikiwyg/Trac.js')
        return handler
    
    # the Genshi template version
    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type
