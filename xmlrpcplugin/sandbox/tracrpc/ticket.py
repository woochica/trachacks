from trac.attachment import Attachment
from trac.core import *
from tracrpc.api import IXMLRPCHandler, expose_rpc
from tracrpc.util import to_timestamp
import trac.ticket.model as model
import trac.ticket.query as query
from trac.ticket.api import TicketSystem
from trac.ticket.notification import TicketNotifyEmail

import time
import pydoc
import xmlrpclib
from StringIO import StringIO

class TicketRPC(Component):
    """ An interface to Trac's ticketing system. """

    implements(IXMLRPCHandler)

    # IXMLRPCHandler methods
    def xmlrpc_namespace(self):
        return 'ticket'

    def xmlrpc_methods(self):
        yield ('TICKET_VIEW', ((list,), (list, str)), self.query)
        yield ('TICKET_VIEW', ((list, xmlrpclib.DateTime),), self.getRecentChanges)
        yield ('TICKET_VIEW', ((list, int),), self.getAvailableActions)
        yield ('TICKET_VIEW', ((list, int),), self.get)
        yield ('TICKET_CREATE', ((int, str, str), (int, str, str, dict), (int, str, str, dict, bool)), self.create)
        yield ('TICKET_APPEND', ((list, int, str), (list, int, str, dict), (list, int, str, dict, bool)), self.update)
        yield ('TICKET_ADMIN', ((None, int),), self.delete)
        yield ('TICKET_VIEW', ((dict, int), (dict, int, int)), self.changeLog)
        yield ('TICKET_VIEW', ((list, int),), self.listAttachments)
        yield ('TICKET_VIEW', ((xmlrpclib.Binary, int, str),), self.getAttachment)
        yield ('TICKET_APPEND',
               ((str, int, str, str, xmlrpclib.Binary, bool),
                (str, int, str, str, xmlrpclib.Binary)),
               self.putAttachment)
        yield ('TICKET_ADMIN', ((bool, int, str),), self.deleteAttachment)
        yield ('TICKET_VIEW', ((list,),), self.getTicketFields)

    # Exported methods
    def query(self, req, qstr='status!=closed'):
        """ Perform a ticket query, returning a list of ticket ID's. """
        q = query.Query.from_string(self.env, qstr)
        out = []
        for t in q.execute(req):
            out.append(t['id'])
        return out

    def getRecentChanges(self, req, since):
        """Returns a list of IDs of tickets that have changed since timestamp."""
        since = to_timestamp(since)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT id FROM ticket'
                       ' WHERE changetime >= %s', (since,))
        result = []
        for row in cursor:
            result.append(int(row[0]))
        return result

    def getAvailableActions(self, req, id):
        """Returns the actions that can be performed on the ticket."""
        ticketSystem = TicketSystem(self.env)
        t = model.Ticket(self.env, id)
        return ticketSystem.get_available_actions(t, req.perm)

    def get(self, req, id):
        """ Fetch a ticket. Returns [id, time_created, time_changed, attributes]. """
        t = model.Ticket(self.env, id)
        return (t.id, t.time_created, t.time_changed, t.values)

    def create(self, req, summary, description, attributes = {}, notify=False):
        """ Create a new ticket, returning the ticket ID. """
        t = model.Ticket(self.env)
        t['status'] = 'new'
        t['summary'] = summary
        t['description'] = description
        t['reporter'] = req.authname or 'anonymous'
        for k, v in attributes.iteritems():
            t[k] = v
        t.insert()

        if notify:
            try:
                tn = TicketNotifyEmail(self.env)
                tn.notify(t, newticket=True)
            except Exception, e:
                self.log.exception("Failure sending notification on creation "
                                   "of ticket #%s: %s" % (t.id, e))
		
        return t.id

    def update(self, req, id, comment, attributes = {}, notify=False):
        """ Update a ticket, returning the new ticket in the same form as getTicket(). """
        now = int(time.time())

        t = model.Ticket(self.env, id)
        for k, v in attributes.iteritems():
            t[k] = v
        t.save_changes(req.authname or 'anonymous', comment)

        if notify:
            try:
                tn = TicketNotifyEmail(self.env)
                tn.notify(t, newticket=False, modtime=now)
            except Exception, e:
                self.log.exception("Failure sending notification on change of "
                                   "ticket #%s: %s" % (t.id, e))

        return self.get(req, t.id)

    def delete(self, req, id):
        """ Delete ticket with the given id. """
        t = model.Ticket(self.env, id)
        t.delete()

    def changeLog(self, req, id, when=0):
        t = model.Ticket(self.env, id)
        return t.get_changelog(when)
    # Use existing documentation from Ticket model
    changeLog.__doc__ = pydoc.getdoc(model.Ticket.get_changelog)

    def listAttachments(self, req, ticket):
        """ Lists attachments for a given ticket. Returns (filename,
        description, size, time, author) for each attachment."""
        for t in Attachment.select(self.env, 'ticket', ticket):
            yield (t.filename, t.description or '', t.size, t.time, t.author)

    def getAttachment(self, req, ticket, filename):
        """ returns the content of an attachment. """
        attachment = Attachment(self.env, 'ticket', ticket, filename)
        return xmlrpclib.Binary(attachment.open().read())

    def putAttachment(self, req, ticket, filename, description, data, replace=True):
        """ Add an attachment, optionally (and defaulting to) overwriting an
        existing one. Returns filename."""
        if not model.Ticket(self.env, ticket).exists:
            raise TracError, 'Ticket "%s" does not exist' % ticket
        if replace:
            try:
                attachment = Attachment(self.env, 'ticket', ticket, filename)
                attachment.delete()
            except TracError:
                pass
        attachment = Attachment(self.env, 'ticket', ticket)
        attachment.author = req.authname or 'anonymous'
        attachment.description = description
        attachment.insert(filename, StringIO(data.data), len(data.data))
        return attachment.filename

    def deleteAttachment(self, req, ticket, filename):
        """ Delete an attachment. """
        if not model.Ticket(self.env, ticket).exists:
            raise TracError('Ticket "%s" does not exists' % ticket)
        attachment = Attachment(self.env, 'ticket', ticket, filename)
        attachment.delete()
        return True

    def getTicketFields(self, req):
        """ Return a list of all ticket fields fields. """
        return TicketSystem(self.env).get_ticket_fields()


def ticketModelFactory(cls, cls_attributes):
    """ Return a class which exports an interface to trac.ticket.model.<cls>. """
    class TicketModelImpl(Component):
        implements(IXMLRPCHandler)

        def xmlrpc_namespace(self):
            return 'ticket.' + cls.__name__.lower()

        def xmlrpc_methods(self):
            yield ('TICKET_VIEW', ((list,),), self.getAll)
            yield ('TICKET_VIEW', ((dict, str),), self.get)
            yield ('TICKET_ADMIN', ((None, str,),), self.delete)
            yield ('TICKET_ADMIN', ((None, str, dict),), self.create)
            yield ('TICKET_ADMIN', ((None, str, dict),), self.update)

        def getAll(self, req):
            for i in cls.select(self.env):
                yield i.name
        getAll.__doc__ = """ Get a list of all ticket %s names. """ % cls.__name__.lower()

        def get(self, req, name):
            i = cls(self.env, name)
            attributes= {}
            for k, default in cls_attributes.iteritems():
                v = getattr(i, k)
                if v is None:
                    v = default
                attributes[k] = v
            return attributes
        get.__doc__ = """ Get a ticket %s. """ % cls.__name__.lower()

        def delete(self, req, name):
            cls(self.env, name).delete()
        delete.__doc__ = """ Delete a ticket %s """ % cls.__name__.lower()

        def create(self, req, name, attributes):
            i = cls(self.env)
            i.name = name
            for k, v in attributes.iteritems():
                setattr(i, k, v)
            i.insert();
        create.__doc__ = """ Create a new ticket %s with the given attributes. """ % cls.__name__.lower()

        def update(self, req, name, attributes):
            self._updateHelper(name, attributes).update()
        update.__doc__ = """ Update ticket %s with the given attributes. """ % cls.__name__.lower()

        def _updateHelper(self, name, attributes):
            i = cls(self.env, name)
            for k, v in attributes.iteritems():
                setattr(i, k, v)
            return i
    TicketModelImpl.__doc__ = """ Interface to ticket %s objects. """ % cls.__name__.lower()
    TicketModelImpl.__name__ = '%sRPC' % cls.__name__
    return TicketModelImpl

def ticketEnumFactory(cls):
    """ Return a class which exports an interface to one of the Trac ticket abstract enum types. """
    class AbstractEnumImpl(Component):
        implements(IXMLRPCHandler)

        def xmlrpc_namespace(self):
            return 'ticket.' + cls.__name__.lower()

        def xmlrpc_methods(self):
            yield ('TICKET_VIEW', ((list,),), self.getAll)
            yield ('TICKET_VIEW', ((str, str),), self.get)
            yield ('TICKET_ADMIN', ((None, str,),), self.delete)
            yield ('TICKET_ADMIN', ((None, str, str),), self.create)
            yield ('TICKET_ADMIN', ((None, str, str),), self.update)

        def getAll(self, req):
            for i in cls.select(self.env):
                yield i.name
        getAll.__doc__ = """ Get a list of all ticket %s names. """ % cls.__name__.lower()

        def get(self, req, name):
            i = cls(self.env, name)
            return i.value
        get.__doc__ = """ Get a ticket %s. """ % cls.__name__.lower()

        def delete(self, req, name):
            cls(self.env, name).delete()
        delete.__doc__ = """ Delete a ticket %s """ % cls.__name__.lower()

        def create(self, req, name, value):
            i = cls(self.env)
            i.name = name
            i.value = value
            i.insert()
        create.__doc__ = """ Create a new ticket %s with the given value. """ % cls.__name__.lower()

        def update(self, req, name, value):
            self._updateHelper(name, value).update()
        update.__doc__ = """ Update ticket %s with the given value. """ % cls.__name__.lower()

        def _updateHelper(self, name, value):
            i = cls(self.env, name)
            i.value = value
            return i

    AbstractEnumImpl.__doc__ = """ Interface to ticket %s. """ % cls.__name__.lower()
    AbstractEnumImpl.__name__ = '%sRPC' % cls.__name__
    return AbstractEnumImpl

ticketModelFactory(model.Component, {'name': '', 'owner': '', 'description': ''})
ticketModelFactory(model.Version, {'name': '', 'time': 0, 'description': ''})
ticketModelFactory(model.Milestone, {'name': '', 'due': 0, 'completed': 0, 'description': ''})

ticketEnumFactory(model.Type)
ticketEnumFactory(model.Status)
ticketEnumFactory(model.Resolution)
ticketEnumFactory(model.Priority)
ticketEnumFactory(model.Severity)
