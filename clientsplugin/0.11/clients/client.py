from trac.core import *
from trac.web.api import IRequestFilter
from trac.ticket.api import ITicketManipulator
from trac.ticket.model import Ticket
from trac.util.html import html, Markup

from genshi.core import Markup
from genshi.builder import tag
from genshi.filters.transform import Transformer 

#from util import *
from clients import model

class ClientModule(Component):
    """Allows for tickets to be assigned to particular clients."""
    
    implements(IRequestFilter)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/ticket/'):
            for field in data['fields']:
                if 'client' == field['name']:
                    field['type'] = 'select'
                    for client in model.Client.select(self.env):
                        field['options'].append(client.name)
                    break
        
        return template, data, content_type
        
    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        pass
        
    def validate_ticket(self, req, ticket):
        # Todo validate client is valid
        pass
        #if req.args.get('action') == 'resolve':
        #    links = TicketLinks(self.env, ticket)
        #    for i in links.blocked_by:
        #        if Ticket(self.env, i)['status'] != 'closed':
        #            yield None, 'Ticket #%s is blocking this ticket'%i

