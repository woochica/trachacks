import re
import trac
from trac.core import *
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import add_script, \
    ITemplateProvider
from pkg_resources import resource_filename
from trac.perm import PermissionSystem

class TicketWebUiAddon(Component):
    implements(IRequestFilter, ITemplateProvider, IRequestHandler)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if re.search('ticket', req.path_info):
            add_script(req, 'cc_selector/cc_selector.js')
        return handler
    
    def post_process_request(self, req, template, content_type):
        return(template, content_type)

    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('cc_selector', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        Genshi templates.
        """
        return [resource_filename(__name__, 'templates')]

    # IRequestHandler
    def match_request(self, req):
        match = re.match(r'^/cc_selector', req.path_info)
        if match:
            return True
        return False

    def process_request(self, req):
        add_script(req, 'cc_selector/cc_selector.js')
        cc_developers = PermissionSystem(self.env).get_users_with_permission('TICKET_VIEW')
        data = {'cc_developers': cc_developers}
        return 'cc_selector.html', data, None
