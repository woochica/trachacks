from trac.core import *
from tracrpc.api import IXMLRPCProvider
import trac.ticket.model as model
import trac.ticket.query as query

class TicketRPC(Component):
    implements(IXMLRPCProvider)

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

    def create_ticket(self, status, summary, description, reporter, cc, type, component, priority, owner, version, milestone, keywords):
        """ Create a new ticket. """
        t = model.Ticket(self.env)
        t['status'] = status
        t['summary'] = summary
        t['description'] = description
        t['reporter'] = reporter
        t['cc'] = cc
        t['type'] = type
        t['component'] = component
        t['priority'] = priority
        t['owner'] = owner
        t['version'] = version
        t['milestone'] = milestone
        t['keywords'] = keywords
        t.insert()
        return self.fetch_ticket(t.id)

    def get_xmlrpc_functions(self):
        yield ('TICKET_VIEW', self.fetch_ticket)
        yield ('TICKET_VIEW', self.query_tickets)
        yield ('TICKET_CREATE', self.create_ticket)
