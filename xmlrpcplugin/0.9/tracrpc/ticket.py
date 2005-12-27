from trac.core import *
from tracrpc.api import AbstractRPCHandler, expose_rpc
import trac.ticket.model as model
import trac.ticket.query as query
import pydoc
import xmlrpclib

class TicketRPC(AbstractRPCHandler):
    """ An interface to Trac's ticketing system. """

    # IXMLRPCHandler methods
    def xmlrpc_namespace(self):
        return 'ticket'

    # Exported methods
    @expose_rpc('TICKET_VIEW', list)
    @expose_rpc('TICKET_VIEW', list, str)
    def query(self, qstr = 'status!=closed'):
        """ Perform a ticket query. Tickets are returned in the same format as getTicket(). """
        q = query.Query.from_string(self.env, qstr)
        out = []
        for t in q.execute():
            out.append(self.getTicket(t['id']))
        return out

    @expose_rpc('TICKET_VIEW', list, int)
    def get(self, id):
        """ Fetch a ticket. Returns [id, time_created, time_changed, attributes]. """
        t = model.Ticket(self.env, id)
        return (t.id, t.time_created, t.time_changed, t.values)

    @expose_rpc('TICKET_CREATE', int, str, str)
    @expose_rpc('TICKET_CREATE', int, str, str, dict)
    def create(self, summary, description, attributes = {}):
        """ Create a new ticket, returning the ticket ID. """
        t = model.Ticket(self.env)
        t['summary'] = summary
        t['description'] = description
        for k, v in attributes.iteritems():
            t[k] = v
        t.insert()
        return t.id

    @expose_rpc('TICKET_APPEND', list, int, str)
    @expose_rpc('TICKET_APPEND', list, int, str, dict)
    def update(self, req, id, comment, attributes = {}):
        """ Update a ticket, returning the new ticket in the same form as getTicket(). """
        t = model.Ticket(self.env, id)
        for k, v in attributes.iteritems():
            t[k] = v
        t.save_changes(req.authname, comment)
        return self.getTicket(t.id)

    @expose_rpc('TICKET_ADMIN', str, int)
    def delete(self, id):
        """ Delete ticket with the given id. """
        t = model.Ticket(self.env, id)
        t.delete()

    @expose_rpc('TICKET_VIEW', dict, int)
    @expose_rpc('TICKET_VIEW', dict, int, int)
    def changeLog(self, id, when = 0):
        t = model.Ticket(self.env, id)
        return t.get_changelog()

    # Use existing documentation from Ticket model
    changeLog.__doc__ = pydoc.getdoc(model.Ticket.get_changelog)


def ticketModelFactory(cls, cls_attributes):
    """ Return a class which exports an interface to trac.ticket.model.<cls>. """
    class TicketModelImpl(AbstractRPCHandler):
        def xmlrpc_namespace(self):
            return 'ticket.' + cls.__name__.lower()

        @expose_rpc('TICKET_VIEW', list)
        def getAll(self):
            for i in cls.select(self.env):
                yield i.name
        getAll.__doc__ = """ Get a list of all ticket %s names. """ % cls.__name__.lower()

        @expose_rpc('TICKET_VIEW', dict, str)
        def get(self, name):
            i = cls(self.env, name)
            attributes= {}
            for k in cls_attributes:
                attributes[k] = getattr(i, k)
            return attr
        get.__doc__ = """ Get a ticket %s. """ % cls.__name__.lower()

        @expose_rpc('TICKET_ADMIN', None, str)
        def delete(self, name):
            cls(self.env, name).delete()
        delete.__doc__ = """ Delete a ticket %s """ % cls.__name__.lower()

        @expose_rpc('TICKET_ADMIN', None, str, dict)
        def create(self, name, attributes):
            self._updateHelper(name, attributes).insert()
        create.__doc__ = """ Create a new ticket %s with the given attributes. """ % cls.__name__.lower()

        @expose_rpc('TICKET_ADMIN', None, str, dict)
        def update(self, name, attributes):
            self._updateHelper(name, attributes).update()
        update.__doc__ = """ Update ticket %s with the given attributes. """ % cls.__name__.lower()

        def _updateHelper(self, name, attributes):
            i = cls(self.env)
            i.name = name
            for k, v in attributes.iteritems():
                setattr(i, k, v)
            return i
    TicketModelImpl.__doc__ = """ Interface to ticket %s objects. """ % cls.__name__.lower()
    TicketModelImpl.__name__ = '%sRPC' % cls.__name__
    return TicketModelImpl

def ticketEnumFactory(cls):
    """ Return a class which exports an interface to one of the Trac ticket abstract enum types. """
    class AbstractEnumImpl(AbstractRPCHandler):
        def xmlrpc_namespace(self):
            return 'ticket.' + cls.__name__.lower()

        @expose_rpc('TICKET_VIEW', list)
        def getAll(self):
            for i in cls.select(self.env):
                yield i.name
        getAll.__doc__ = """ Get a list of all ticket %s names. """ % cls.__name__.lower()

        @expose_rpc('TICKET_VIEW', str, str)
        def get(self, name):
            i = cls(self.env, name)
            return i.value
        get.__doc__ = """ Get a ticket %s. """ % cls.__name__.lower()

        @expose_rpc('TICKET_ADMIN', None, str)
        def delete(self, name):
            cls(self.env, name).delete()
        delete.__doc__ = """ Delete a ticket %s """ % cls.__name__.lower()

        @expose_rpc('TICKET_ADMIN', None, str, str)
        def create(self, name, value):
            self._updateHelper(name, value).insert()
        create.__doc__ = """ Create a new ticket %s with the given value. """ % cls.__name__.lower()

        @expose_rpc('TICKET_ADMIN', None, str, str)
        def update(self, name, value):
            self._updateHelper(name, value).update()
        update.__doc__ = """ Update ticket %s with the given value. """ % cls.__name__.lower()

        def _updateHelper(self, name, value):
            i = cls(self.env)
            i.name = name
            i.value = value
            return i

    AbstractEnumImpl.__doc__ = """ Interface to ticket %s. """ % cls.__name__.lower()
    AbstractEnumImpl.__name__ = '%sRPC' % cls.__name__
    return AbstractEnumImpl

ticketModelFactory(model.Component, ('name', 'owner', 'description'))
ticketModelFactory(model.Version, ('name', 'time', 'description'))
ticketModelFactory(model.Milestone, ('name', 'due', 'completed', 'description'))

ticketEnumFactory(model.Type)
ticketEnumFactory(model.Status)
ticketEnumFactory(model.Resolution)
ticketEnumFactory(model.Priority)
ticketEnumFactory(model.Severity)
