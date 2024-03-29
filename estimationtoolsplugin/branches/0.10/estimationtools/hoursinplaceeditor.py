from estimationtools.utils import get_estimation_field
from pkg_resources import resource_filename
from trac.core import implements, Component
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_script

class HoursInPlaceEditor(Component):
    """A filter to implement in-place editing for estimated hours field in query page.
    
    Requires Trac XML-RPC Plug-in.
    """

    implements(IRequestFilter, IRequestHandler, ITemplateProvider)
    
    estimation_field = get_estimation_field()
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/estimationtools')

    def process_request(self, req):
        req.hdf['edithours.field'] = self.estimation_field
        
        return 'edithours.cs', 'text/javascript' 

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
            
    def post_process_request(self, req, template, content_type):
        if (req.path_info.startswith('/query')
            and req.perm.has_permission('TICKET_MODIFY') 
            and req.perm.has_permission('XML_RPC')):
            add_script(req, 'estimationtools/jquery-1.2.3.min.js')
            add_script(req, 'estimationtools/jquery.jeditable.mini.js')
            idx = 0
            while True:
                js = req.hdf.get('chrome.scripts.%i.href'%idx)
                if not js:
                    break
                idx += 1
            req.hdf['chrome.scripts.%i' % idx] = {
                'href': req.href.estimationtools('edithours.js'), 
                'type': 'text/javascript',
            }
        return template, content_type

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('estimationtools', resource_filename(__name__, 'htdocs'))]
            
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]
