
import xmlrpclib

from trac.core import *
from tracrpc.api import IXMLRPCHandler
import trac.ticket.model as model

class TicketExtRPC(Component):
    """ Additional Ticket XML-RPC API. """

    implements(IXMLRPCHandler)

    def xmlrpc_namespace(self):
        return 'ticketext'

    def xmlrpc_methods(self):
        yield ('TICKET_VIEW', 
                   ((list, int, str, str, dict),), 
                   self.update)
        
    def update(self, req, id, author, comment, attributes):
        """ Update a ticket, returning the new ticket in the same form as getTicket(). """
        t = model.Ticket(self.env, id)
        for k, v in attributes.iteritems():
            t[k] = v
        t.save_changes(author or req.authname or 'anonymous', comment)
        return []