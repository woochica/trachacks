#
#   Trac plugin goo to link up checklist with Trac
#

import re
from trac.core import *
from trac.web import IRequestHandler
from genshi.builder import tag

class ChecklistUpdaterComponent(Component):
    implements(IRequestHandler)

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.endswith('/checklist/update')

    def process_request(self, req):
        req.send_response(200)
        req.send_header('Content-Type', 'text/plain')
        req.end_headers()
        req.write('Howdy')

