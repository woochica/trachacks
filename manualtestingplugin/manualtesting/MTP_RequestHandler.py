# ManualTesting.MTP_RequestHandler

import re
from trac.core import *
from trac.web.main import IRequestHandler
from trac.web.chrome import add_stylesheet
from trac.util import escape
from manualtesting.ManualTestingAPI import *

"""
Extension point interface for request handlers."""
class MTP_RequestHandler(Component):
    implements(IRequestHandler)

    """
    Return whether the handler wants to process the given request."""
    def match_request(self, req):
        # return req.path_info == '/testing'
        match = re.match('/testing', req.path_info)
        if match:
            return True

    """
    Process the request. Should return a (template_name, content_type)
    tuple, where `template` is the ClearSilver template to use (either
    a `neo_cs.CS` object, or the file name of the template), and
    `content_type` is the MIME type of the content. If `content_type` is
    `None`, "text/html" is assumed.

    Note that if template processing should not occur, this method can
    simply send the response itself and not return anything."""
    def process_request(self, req):
        add_stylesheet(req, 'mt/css/manualtesting.css')

        # Prepare request object
        # req.args['component'] = 'core'

        # Get database access
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Return page content
        mtAPI = ManualTestingAPI(self, req)
        content = mtAPI.render(req, cursor)
        # db.commit()

        return content