# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2008 ::: Alec Thomas (alec@swapoff.org)
(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import inspect
from datetime import datetime

import genshi

from trac.attachment import Attachment
from trac.core import *
from trac.perm import PermissionError
from trac.resource import Resource, ResourceNotFound
import trac.ticket.model as model
import trac.ticket.query as query
from trac.ticket.api import TicketSystem
from trac.ticket.notification import TicketNotifyEmail
from trac.ticket.web_ui import TicketModule
from trac.web.chrome import add_warning
from trac.util.datefmt import to_datetime, utc

from tracrpc.api import IXMLRPCHandler, expose_rpc, Binary
from tracrpc.util import StringIO, to_utimestamp, from_utimestamp

__all__ = ['TicketRPC']

class TicketRPC(Component):
    """ An interface to Trac's ticketing system. """

    implements(IXMLRPCHandler)

    # IXMLRPCHandler methods
    def xmlrpc_namespace(self):
        return 'ticket'

    def xmlrpc_methods(self):
        yield (None, ((list,), (list, str)), self.query)
        yield (None, ((list, datetime),), self.getRecentChanges)
        yield (None, ((list, int),), self.getAvailableActions)
        yield (None, ((list, int),), self.getActions)
        yield (None, ((list, int),), self.get)
        yield ('TICKET_CREATE', ((int, str, str),
                                 (int, str, str, dict),
                                 (int, str, str, dict, bool),
                                 (int, str, str, dict, bool, datetime)),
                      self.create)
        yield (None, ((list, int, str),
                      (list, int, str, dict),
                      (list, int, str, dict, bool),
                      (list, int, str, dict, bool, str),
                      (list, int, str, dict, bool, str, datetime)),
                      self.update)
        yield (None, ((None, int),), self.delete)
        yield (None, ((dict, int), (dict, int, int)), self.changeLog)
        yield (None, ((list, int),), self.listAttachments)
        yield (None, ((Binary, int, str),), self.getAttachment)
        yield (None,
               ((str, int, str, str, Binary, bool),
                (str, int, str, str, Binary)),
               self.putAttachment)
        yield (None, ((bool, int, str),), self.deleteAttachment)
        yield ('TICKET_VIEW', ((list,),), self.getTicketFields)

    # Exported methods
    def query(self, req, qstr='status!=closed'):
        """
        Perform a ticket query, returning a list of ticket ID's.
        All queries will use stored settings for maximum number of results per
        page and paging options. Use `max=n` to define number of results to
        receive, and use `page=n` to page through larger result sets. Using
        `max=0` will turn off paging and return all results.
        """
        q = query.Query.from_string(self.env, qstr)
        ticket_realm = Resource('ticket')
        out = []
        for t in q.execute(req):
            tid = t['id']
            if 'TICKET_VIEW' in req.perm(ticket_realm(id=tid)):
                out.append(tid)
        return out

    def getRecentChanges(self, req, since):
        """Returns a list of IDs of tickets that have changed since timestamp."""
        since = to_utimestamp(since)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT id FROM ticket'
                       ' WHERE changetime >= %s', (since,))
        result = []
        ticket_realm = Resource('ticket')
        for row in cursor:
            tid = int(row[0])
            if 'TICKET_VIEW' in req.perm(ticket_realm(id=tid)):
                result.append(tid)
        return result

    def getAvailableActions(self, req, id):
        """ Deprecated - will be removed. Replaced by `getActions()`. """
        self.log.warning("Rpc ticket.getAvailableActions is deprecated")
        return [action[0] for action in self.getActions(req, id)]

    def getActions(self, req, id):
        """Returns the actions that can be performed on the ticket as a list of
        `[action, label, hints, [input_fields]]` elements, where `input_fields` is
        a list of `[name, value, [options]]` for any required action inputs."""
        ts = TicketSystem(self.env)
        t = model.Ticket(self.env, id)
        actions = []
        for action in ts.get_available_actions(req, t):
            fragment = genshi.builder.Fragment()
            hints = []
            first_label = None
            for controller in ts.action_controllers:
                if action in [c_action for c_weight, c_action \
                                in controller.get_ticket_actions(req, t)]:
                    label, widget, hint = \
                        controller.render_ticket_action_control(req, t, action)
                    fragment += widget
                    hints.append(hint.rstrip('.') + '.')
                    first_label = first_label == None and label or first_label
            controls = []
            for elem in fragment.children:
                if not isinstance(elem, genshi.builder.Element):
                    continue
                if elem.tag == 'input':
                    controls.append((elem.attrib.get('name'),
                                    elem.attrib.get('value'), []))
                elif elem.tag == 'select':
                    value = ''
                    options = []
                    for opt in elem.children:
                        if not (opt.tag == 'option' and opt.children):
                            continue
                        option = opt.children[0]
                        options.append(option)
                        if opt.attrib.get('selected'):
                            value = option
                    controls.append((elem.attrib.get('name'),
                                    value, options))
            actions.append((action, first_label, " ".join(hints), controls))
        return actions

    def get(self, req, id):
        """ Fetch a ticket. Returns [id, time_created, time_changed, attributes]. """
        t = model.Ticket(self.env, id)
        req.perm(t.resource).require('TICKET_VIEW')
        t['_ts'] = str(to_utimestamp(t.time_changed))
        return (t.id, t.time_created, t.time_changed, t.values)

    def create(self, req, summary, description, attributes={}, notify=False, when=None):
        """ Create a new ticket, returning the ticket ID.
        Overriding 'when' requires admin permission. """
        t = model.Ticket(self.env)
        t['summary'] = summary
        t['description'] = description
        t['reporter'] = req.authname
        for k, v in attributes.iteritems():
            t[k] = v
        t['status'] = 'new'
        t['resolution'] = ''
        # custom create timestamp?
        if when and not 'TICKET_ADMIN' in req.perm:
            self.log.warn("RPC ticket.create: %r not allowed to create with "
                    "non-current timestamp (%r)", req.authname, when)
            when = None
        t.insert(when=when)
        if notify:
            try:
                tn = TicketNotifyEmail(self.env)
                tn.notify(t, newticket=True)
            except Exception, e:
                self.log.exception("Failure sending notification on creation "
                                   "of ticket #%s: %s" % (t.id, e))
        return t.id

    def update(self, req, id, comment, attributes={}, notify=False, author='', when=None):
        """ Update a ticket, returning the new ticket in the same form as
        get(). 'New-style' call requires two additional items in attributes:
        (1) 'action' for workflow support (including any supporting fields
        as retrieved by getActions()),
        (2) '_ts' changetime token for detecting update collisions (as received
        from get() or update() calls).
        ''Calling update without 'action' and '_ts' changetime token is
        deprecated, and will raise errors in a future version.'' """
        t = model.Ticket(self.env, id)
        # custom author?
        if author and not (req.authname == 'anonymous' \
                            or 'TICKET_ADMIN' in req.perm(t.resource)):
            # only allow custom author if anonymous is permitted or user is admin
            self.log.warn("RPC ticket.update: %r not allowed to change author "
                    "to %r for comment on #%d", req.authname, author, id)
            author = ''
        author = author or req.authname
        # custom change timestamp?
        if when and not 'TICKET_ADMIN' in req.perm(t.resource):
            self.log.warn("RPC ticket.update: %r not allowed to update #%d with "
                    "non-current timestamp (%r)", author, id, when)
            when = None
        when = when or to_datetime(None, utc)
        # and action...
        if not 'action' in attributes:
            # FIXME: Old, non-restricted update - remove soon!
            self.log.warning("Rpc ticket.update for ticket %d by user %s " \
                    "has no workflow 'action'." % (id, req.authname))
            req.perm(t.resource).require('TICKET_MODIFY')
            time_changed = attributes.pop('_ts', None)
            if time_changed and \
                    str(time_changed) != str(to_utimestamp(t.time_changed)):
                raise TracError("Ticket has been updated since last get().")
            for k, v in attributes.iteritems():
                t[k] = v
            t.save_changes(author, comment, when=when)
        else:
            ts = TicketSystem(self.env)
            tm = TicketModule(self.env)
            # TODO: Deprecate update without time_changed timestamp
            time_changed = attributes.pop('_ts', to_utimestamp(t.time_changed))
            try:
                time_changed = int(time_changed)
            except ValueError:
                raise TracError("RPC ticket.update: Wrong '_ts' token " \
                                "in attributes (%r)." % time_changed)
            action = attributes.get('action')
            avail_actions = ts.get_available_actions(req, t)
            if not action in avail_actions:
                raise TracError("Rpc: Ticket %d by %s " \
                        "invalid action '%s'" % (id, req.authname, action))
            controllers = list(tm._get_action_controllers(req, t, action))
            all_fields = [field['name'] for field in ts.get_ticket_fields()]
            for k, v in attributes.iteritems():
                if k in all_fields and k != 'status':
                    t[k] = v
            # TicketModule reads req.args - need to move things there...
            req.args.update(attributes)
            req.args['comment'] = comment
            # Collision detection: 0.11+0.12 timestamp
            req.args['ts'] = str(from_utimestamp(time_changed))
            # Collision detection: 0.13/1.0+ timestamp
            req.args['view_time'] = str(time_changed)
            changes, problems = tm.get_ticket_changes(req, t, action)
            for warning in problems:
                add_warning(req, "Rpc ticket.update: %s" % warning)
            valid = problems and False or tm._validate_ticket(req, t)
            if not valid:
                raise TracError(
                    " ".join([warning for warning in req.chrome['warnings']]))
            else:
                tm._apply_ticket_changes(t, changes)
                self.log.debug("Rpc ticket.update save: %s" % repr(t.values))
                t.save_changes(author, comment, when=when)
                # Apply workflow side-effects
                for controller in controllers:
                    controller.apply_action_side_effects(req, t, action)
        if notify:
            try:
                tn = TicketNotifyEmail(self.env)
                tn.notify(t, newticket=False, modtime=when)
            except Exception, e:
                self.log.exception("Failure sending notification on change of "
                                   "ticket #%s: %s" % (t.id, e))
        return self.get(req, t.id)

    def delete(self, req, id):
        """ Delete ticket with the given id. """
        t = model.Ticket(self.env, id)
        req.perm(t.resource).require('TICKET_ADMIN')
        t.delete()

    def changeLog(self, req, id, when=0):
        t = model.Ticket(self.env, id)
        req.perm(t.resource).require('TICKET_VIEW')
        for date, author, field, old, new, permanent in t.get_changelog(when):
            yield (date, author, field, old, new, permanent)
    # Use existing documentation from Ticket model
    changeLog.__doc__ = inspect.getdoc(model.Ticket.get_changelog)

    def listAttachments(self, req, ticket):
        """ Lists attachments for a given ticket. Returns (filename,
        description, size, time, author) for each attachment."""
        attachments = []
        for a in Attachment.select(self.env, 'ticket', ticket):
            if 'ATTACHMENT_VIEW' in req.perm(a.resource):
                yield (a.filename, a.description, a.size, a.date, a.author)

    def getAttachment(self, req, ticket, filename):
        """ returns the content of an attachment. """
        attachment = Attachment(self.env, 'ticket', ticket, filename)
        req.perm(attachment.resource).require('ATTACHMENT_VIEW')
        return Binary(attachment.open().read())

    def putAttachment(self, req, ticket, filename, description, data, replace=True):
        """ Add an attachment, optionally (and defaulting to) overwriting an
        existing one. Returns filename."""
        if not model.Ticket(self.env, ticket).exists:
            raise ResourceNotFound('Ticket "%s" does not exist' % ticket)
        if replace:
            try:
                attachment = Attachment(self.env, 'ticket', ticket, filename)
                req.perm(attachment.resource).require('ATTACHMENT_DELETE')
                attachment.delete()
            except TracError:
                pass
        attachment = Attachment(self.env, 'ticket', ticket)
        req.perm(attachment.resource).require('ATTACHMENT_CREATE')
        attachment.author = req.authname
        attachment.description = description
        attachment.insert(filename, StringIO(data.data), len(data.data))
        return attachment.filename

    def deleteAttachment(self, req, ticket, filename):
        """ Delete an attachment. """
        if not model.Ticket(self.env, ticket).exists:
            raise ResourceNotFound('Ticket "%s" does not exists' % ticket)
        attachment = Attachment(self.env, 'ticket', ticket, filename)
        req.perm(attachment.resource).require('ATTACHMENT_DELETE')
        attachment.delete()
        return True

    def getTicketFields(self, req):
        """ Return a list of all ticket fields fields. """
        return TicketSystem(self.env).get_ticket_fields()

class StatusRPC(Component):
    """ An interface to Trac ticket status objects.
    Note: Status is defined by workflow, and all methods except `getAll()`
    are deprecated no-op methods - these will be removed later. """

    implements(IXMLRPCHandler)

    # IXMLRPCHandler methods
    def xmlrpc_namespace(self):
        return 'ticket.status'

    def xmlrpc_methods(self):
        yield ('TICKET_VIEW', ((list,),), self.getAll)
        yield ('TICKET_VIEW', ((dict, str),), self.get)
        yield ('TICKET_ADMIN', ((None, str,),), self.delete)
        yield ('TICKET_ADMIN', ((None, str, dict),), self.create)
        yield ('TICKET_ADMIN', ((None, str, dict),), self.update)

    def getAll(self, req):
        """ Returns all ticket states described by active workflow. """
        return TicketSystem(self.env).get_all_status()
    
    def get(self, req, name):
        """ Deprecated no-op method. Do not use. """
        # FIXME: Remove
        return '0'

    def delete(self, req, name):
        """ Deprecated no-op method. Do not use. """
        # FIXME: Remove
        return 0

    def create(self, req, name, attributes):
        """ Deprecated no-op method. Do not use. """
        # FIXME: Remove
        return 0

    def update(self, req, name, attributes):
        """ Deprecated no-op method. Do not use. """
        # FIXME: Remove
        return 0

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
            if (cls.__name__ == 'Status'):
               i = cls(self.env)
               x = name
            else: 
               i = cls(self.env, name)
               x = i.value
            return x
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
ticketEnumFactory(model.Resolution)
ticketEnumFactory(model.Priority)
ticketEnumFactory(model.Severity)
