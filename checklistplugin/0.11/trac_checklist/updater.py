#
#   updater.py
#
#   Manages the updating of the database by AJAX call.
#

import re, sys
from trac.core import *
from trac.web import IRequestHandler
from genshi.builder import tag

class BadRequest(Exception):
    __http_status__ = 400

class PermissionDenied(Exception):
    __http_status__ = 401

class ChecklistUpdaterComponent(Component):
    """
    Used as an AJAX request handler, updates the database with the information
    provided to .../checklist/update.  The information contained is:

    __context__ : The context string to use for the fields provided.

    All other query items are the checklist items that are turned "on".  These
    are then applied to the database.  The following response codes are
    produced by this URL:

    200 "OK"
        Operation successful.

    400 Problem message
        Indicates the input query could not be processed.

    401 "User %s cannot set %s."
        User is not allowed to complete the transaction.

    500 Exception type: error message
        A Python exception was encountered.
    """

    implements(IRequestHandler)

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.endswith('/checklist/update')

    def process_request(self, req):
        try:
            context = req.args.get('__context__')
            if context is None:
                raise BadRequest('__context__ is required')
        except Exception, e:
            code = getattr(e, '__http_status__', 500)
            msg = str(e)
            if code == 500:
                msg = e.__class__.__name__ + ': ' + msg
            req.send_response(code)
            req.send_header('Content-Type', 'text/plain')
            req.end_headers()
            req.write(msg)
        else:
            req.send_response(200)
            req.send_header('Content-Type', 'text/plain')
            req.end_headers()
            req.write('OK')


