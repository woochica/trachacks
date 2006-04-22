from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet, Chrome

import os
import os.path
from turbostan.stansupport import TurboStan
from pkg_resources import resource_filename

__all__ = ['StatusPage']

class StatusPage(Component):
    """
        Provides functions related to registration
    """

    implements(IRequestHandler, ITemplateProvider)

    def match_request(self, req):
        self.log.info(str(req.args))
        return req.path_info == '/status'

    def process_request(self, req):
        add_stylesheet(req, 'aftracistan/css/aftracistan.css')
        data = { 'name': 'Pacopablo',
                 'message' : 'Hello vatos!',
                 'title' : 'Pyrus',
               }
        resp = {'template': 'index',
                'engine'  : 'stan',
                'content_type': 'text/html',
                'info': data}
        print str(self.get_templates_dirs())
        return resp

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


