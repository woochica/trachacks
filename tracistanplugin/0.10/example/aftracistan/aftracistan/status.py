from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet, Chrome

import os
import os.path
from pkg_resources import resource_filename
from tracistan import IStanRequestHandler

__all__ = ['StatusPage']

class StatusPage(Component):
    """
        Provides functions related to registration
    """

    implements(IStanRequestHandler, ITemplateProvider)

    def match_request(self, req):
        self.log.info(str(req.args))
        return req.path_info == '/status'

    def process_request(self, req):
        add_stylesheet(req, 'aftracistan/css/aftracistan.css')
        req.standata = { 'name': 'Pacopablo',
                 'message' : 'Hello vatos!',
                 'title' : 'Pyrus',
               }
        return ('index.stan', None)

    def get_templates_dirs(self):
        """
            Return the absolute path of the directory containing the provided
            templates
        """
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return [('aftracistan', resource_filename(__name__, 'htdocs'))]


