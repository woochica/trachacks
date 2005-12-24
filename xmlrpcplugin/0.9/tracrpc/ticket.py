from trac.core import *
from tracrpc.api import IXMLRPCHandler
import trac.ticket.model as model
import trac.ticket.query as query
import pydoc

class TicketRPC(Component):
    """ An interface to Trac's ticketing system. """

    implements(IXMLRPCHandler)

    # IXMLRPCHandler methods
    def xmlrpc_namespace(self):
        return 'ticket'

    def xmlrpc_procedures(self):
        yield ('TICKET_VIEW', self.getTicket)
        yield ('TICKET_VIEW', self.queryTickets)
        yield ('TICKET_CREATE', self.createTicket)
        yield ('TICKET_APPEND', self.updateTicket)
        yield ('TICKET_ADMIN', self.deleteTicket)
        yield ('TICKET_VIEW', self.ticketChangelog)

    # Exported procedures
    def queryTickets(self, qstr = 'status!=closed'):
        """ Perform a ticket query. Tickets are returned in the same format as getTicket(). """
        q = query.Query.from_string(self.env, qstr)
        out = []
        for t in q.execute():
            out.append(self.getTicket(t['id']))
        return out

    def getTicket(self, id):
        """ Fetch a ticket. Returns [id, time_created, time_changed, values], where
            values is a dictionary of ticket values. """
        t = model.Ticket(self.env, id)
        return (t.id, t.time_created, t.time_changed, t.values)

    def createTicket(self, summary, description, values = {}):
        """ Create a new ticket, returning the new ticket in the same form as getTicket(). """
        t = model.Ticket(self.env)
        t['summary'] = summary
        t['description'] = description
        for k, v in values.iteritems():
            t[k] = v
        t.insert()
        return self.getTicket(t.id)

    def updateTicket(self, req, id, comment, values = {}):
        """ Update a ticket, returning the new ticket in the same form as getTicket(). """
        t = model.Ticket(self.env, id)
        for k, v in values.iteritems():
            t[k] = v
        t.save_changes(req.authname, comment)
        return self.getTicket(t.id)

    def deleteTicket(self, id):
        """ Delete ticket with the given id. """
        t = model.Ticket(self.env, id)
        t.delete()

    def ticketChangelog(self, id, when = 0):
        t = model.Ticket(self.env, id)
        return t.ticketChangelog()

    # Use existing documentation from Ticket model
    ticketChangelog.__doc__ = pydoc.getdoc(model.Ticket.get_changelog)
