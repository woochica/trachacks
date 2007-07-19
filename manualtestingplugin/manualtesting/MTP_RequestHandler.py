# ManualTesting.MTP_RequestHandler

from trac.core import *
from trac.web.main import IRequestHandler
from trac.web.chrome import add_stylesheet
from trac.util import escape

class MTP_RequestHandler(Component):
    implements(IRequestHandler)

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/testing'

    def process_request(self, req):
        add_stylesheet(req, 'mt/css/manualtesting.css')
        return 'testing.cs', None