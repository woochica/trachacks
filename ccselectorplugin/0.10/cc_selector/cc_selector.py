import re
from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script, \
    ITemplateProvider

import trac


class TicketWebUiAddon(Component):
    implements(IRequestFilter, ITemplateProvider)
    
    def __init__(self):
        pass

    # IRequestFilter methods
    # for trac 0.10 we call add_script in post_process_request
    # for trac 0.11 we call add_script in pre_process_request
    def pre_process_request(self, req, handler):
        if trac.__version__.startswith('0.11'):
            if re.search('ticket', req.path_info):
                add_script(req, 'cc_selector/cc_selector.js')
        return handler
    def post_process_request(self, req, template, content_type):
        if trac.__version__.startswith('0.10'):
            if re.search('ticket', req.path_info):
                add_script(req, 'cc_selector/cc_selector.js')
        return(template, content_type)

    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('cc_selector', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        return []
