"""
AdminEnumListPlugin:
a plugin for Trac
http://trac.edgewall.org

(C) Stepan Riha, 2009
"""

from trac.core import *

from pkg_resources import resource_filename
from trac import __version__ as VERSION
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.web.chrome import (
    Chrome, ITemplateProvider, add_script, add_stylesheet, add_notice,
    add_warning
)

class AdminEnumListPlugin(Component):

    implements(ITemplateStreamFilter, IRequestFilter, ITemplateProvider)
    
    
    ### methods for IRequestFilter
    
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/admin/'):
            add_script(req, 'adminenumlistplugin/adminenumlist.js')
            if VERSION < '1.0':
                add_script(req, 'adminenumlistplugin/jquery-ui-custom.js')
            else:
                Chrome(self.env).add_jquery_ui(req)

        return template, data, content_type
    

    ### methods for ITemplateStreamFilter

    """Filter a Genshi event stream prior to rendering."""

    def filter_stream(self, req, method, filename, stream, data):
        """Return a filtered Genshi event stream, or the original unfiltered
        stream if no match.

        `req` is the current request object, `method` is the Genshi render
        method (xml, xhtml or text), `filename` is the filename of the template
        to be rendered, `stream` is the event stream and `data` is the data for
        the current template.

        See the Genshi documentation for more information.
        """
        
        return stream

    ### methods for ITemplateProvider

    def get_htdocs_dirs(self):
        return [('adminenumlistplugin', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
 
