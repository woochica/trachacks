"""
Open311:
a plugin for Trac that implements the DC open311 API 
http://api.dc.gov/open311/v1
"""

import simplejson

from trac.config import Option
from trac.core import *
from trac.ticket import model
from trac.ticket import Ticket
from trac.ticket import TicketSystem
from trac.web.api import IRequestHandler

class Open311(Component):

    implements(IRequestHandler)

    # custom ticket field for AID
    # see: http://api.dc.gov/geocoding/v1
    aid = Option('ticket-custom', 'aid', 'text')
    aid_label = Option('ticket-custom', 'aid.label', 'AID')

    ### methods for IRequestHandler

    """Extension point interface for request handlers."""

    methods = { 'meta_getTypesList': ['GET'],
                 'meta_getTypeDefinition': ['GET'],
                 'get': ['GET'],
                 'submit': ['POST'],
                 'getFromToken': ['GET'],
                 }

    formats = [ 'json', 'xml' ] # TODO: formatters

    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        
        path = req.path_info.strip('/').split('/')
        if path and '.' in path[0]:
            method, format = path[0].split('.', 1)
            if not (method in self.methods and format in self.formats):
                return False
            if req.method in self.methods[method]:
                return True
        return False


    def process_request(self, req):
        """Process the request. For ClearSilver, return a (template_name,
        content_type) tuple, where `template` is the ClearSilver template to use
        (either a `neo_cs.CS` object, or the file name of the template), and
        `content_type` is the MIME type of the content. For Genshi, return a
        (template_name, data, content_type) tuple, where `data` is a dictionary
        of substitutions for the template.

        For both templating systems, "text/html" is assumed if `content_type` is
        `None`.

        Note that if template processing should not occur, this method can
        simply send the response itself and not return anything.
        """

        # get the method and format
        path = req.path_info.strip('/').split('/')
        method, format = path[0].split('.', 1)
        method = getattr(self, method, self.error)

        # execute the method
        try:
            output = method(req)
        except Exception, e:
            output = { 'error': str(e) }
            
        # format output
        if format == 'json':
            output = simplejson.dumps(output)
            content_type = 'application/json'
        else:
            output = '<msg>n/a</msg>'
            content_type = 'text/xml'

        # send the response
        req.send(output, content_type=content_type)

    def error(self, req):
        return { 'error': 'something bad happened' }

    ### DC geocoding API methods: see http://api.dc.gov/geocoding/v1

    ### DC open311 API methods: see http://api.dc.gov/open311/v1

    def meta_getTypesList(self, req):
        types = [ { 'servicetype': val.name, 'servicecode': val.value } for val in model.Type.select(self.env) ]
        return { 'servicetypeslist': types }

    def meta_getTypeDefinition(self, req):
        ticket_system = TicketSystem(self.env)
        fields = ticket_system.get_ticket_fields()
        
        # remove ticket type as this should be a parameter of the request
        # XXX Trac doesn't support fields based on ticket type
        fields = [ field for field in fields 
                   if field['name'] != 'type' ]
        return fields

    def get(self, req):
        ticket_id = req.args.get('servicerequestid')
        if not ticket_id:
            return None
        ticket = Ticket(self.env, int(ticket_id))
        fields = []

        # mapping -- not yet complete
        fields.append({'servicerequestid': ticket.id})
        fields.append({"servicepriority": ticket['priority']})
        fields.append({'serviceorderdate': str(ticket.time_created)})
        fields.append({"serviceorderstatus": ticket['status']})
        fields.append({'resolution': ticket['resolution']})
        fields.append({"aid": ticket['aid']})

        return { 'servicerequest': fields }

    def submit(self, req):
        raise NotImplementedError

    def getFromToken(self, req):
        # XXX for now return the same token as the request (no temporaries)
        token = req.args['token']
        return {"servicerequestid": token}
