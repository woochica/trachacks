from trac.core import *
from tracrpc.api import IXMLRPCHandler
import trac.ticket.model as model
import trac.ticket.query as query
import pydoc

class TicketRPC(Component):
    implements(IXMLRPCHandler)

    # IXMLRPCHandler methods
    def get_xmlrpc_functions(self):
        yield ('TICKET_VIEW', self.fetch_ticket)
        yield ('TICKET_VIEW', self.query_tickets)
        yield ('TICKET_CREATE', self.create_ticket)
        yield ('TICKET_APPEND', self.update_ticket)
        yield ('TICKET_ADMIN', self.delete_ticket)
        yield ('TICKET_VIEW', self.get_changelog)
        yield ('TICKET_VIEW', self.get_components)
        yield ('TICKET_VIEW', self.get_milestones)

    # Exported procedures
    def query_tickets(self, qstr = 'status!=closed'):
        """ Perform a ticket query. Tickets are returned in the same format as fetch_ticket(). """
        q = query.Query.from_string(self.env, qstr)
        out = []
        for t in q.execute():
            out.append(self.fetch_ticket(t['id']))
        return out

    def fetch_ticket(self, id):
        """ Fetch a ticket. Returns [id, time_created, time_changed, values], where
            values is a dictionary of ticket values. """
        t = model.Ticket(self.env, id)
        return (t.id, t.time_created, t.time_changed, t.values)

    def create_ticket(self, summary, description, values = {}):
        """ Create a new ticket, returning the new ticket in the same form as fetch_ticket(). """
        t = model.Ticket(self.env)
        t['summary'] = summary
        t['description'] = description
        t.values.update(values)
        t.insert()
        return self.fetch_ticket(t.id)

    def update_ticket(self, req, id, comment, values = {}):
        """ Update a ticket, returning the new ticket in the same form as fetch_ticket(). """
        t = model.Ticket(self.env, id)
        t.values.update(values)
        t.save_changes(req.authname, comment)
        return self.fetch_ticket(t.id)

    def delete_ticket(self, id):
        """ Delete ticket with the given id. """
        t = model.Ticket(self.env, id)
        t.delete()

    def get_changelog(self, id, when = 0):
        t = model.Ticket(self.env, id)
        return t.get_changelog()

    # Use existing documentation from Ticket model
    get_changelog.__doc__ = pydoc.getdoc(model.Ticket.get_changelog)
