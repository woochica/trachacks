# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Alec Thomas <alec@swapoff.org>
# Copyright (C) 2011-2013 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from trac.config import BoolOption, ListOption
from trac.core import Component, implements
from trac.perm import PermissionError
from trac.resource import Resource
from trac.test import Mock, MockPerm
from trac.ticket.api import ITicketChangeListener, TicketSystem
from trac.ticket.model import Ticket
from trac.util import get_reporter_id
from trac.util.compat import all, any, groupby
from trac.util.text import to_unicode

from tractags.api import DefaultTagProvider, ITagProvider, TagSystem, _


class TicketTagProvider(DefaultTagProvider):
    """A tag provider using ticket fields as sources of tags.

    Relevant ticket data is initially copied to plugin's own tag db store for
    more efficient regular access, that matters especially when working with
    large ticket quantities, kept current using ticket change listener events.

    Currently does NOT support custom fields.
    """

    implements(ITicketChangeListener)

#    custom_fields = ListOption('tags', 'custom_ticket_fields',
#        doc=_("List of custom ticket fields to expose as tags."))

    fields = ListOption('tags', 'ticket_fields', 'keywords',
        doc=_("List of ticket fields to expose as tags."))

    ignore_closed_tickets = BoolOption('tags', 'ignore_closed_tickets', True,
        _("Do not collect tags from closed tickets."))

    map = {'view': 'TICKET_VIEW', 'modify': 'TICKET_CHGPROP'}
    realm = 'ticket'
    use_cache = False

    def __init__(self):
        self._fetch_tkt_tags()
        cfg = self.config
        cfg_key = 'permission_policies'
        default_policies = cfg.defaults().get('trac', {}).get(cfg_key)
        self.fast_permcheck = all(p in default_policies for
                                  p in cfg.get('trac', cfg_key))

    def _check_permission(self, req, resource, action):
        """Optionally coarse-grained permission check."""
        if self.fast_permcheck or not (resource and resource.id):
            perm = req.perm('ticket')
        else:
            perm = req.perm(resource)
        return self.check_permission(perm, action) and \
               self.map[action] in perm

    def get_tagged_resources(self, req, tags):
        if not self._check_permission(req, None, 'view'):
            return

        if not tags:
            # Cache 'all tagged resources' for better performance.
            for resource, tags in self._tagged_resources:
                if self.fast_permcheck or \
                        self._check_permission(req, resource, 'view'):
                    yield resource, tags
        else:
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            sql = """
                SELECT name, tag
                  FROM tags
                 WHERE tagspace=%%s
                   AND tags.tag IN (%s)
                 ORDER by name
            """ % ', '.join(['%s' for t in tags])
            args = [self.realm] + list(tags)
            cursor.execute(sql, args)
            for name, tags in groupby(cursor, lambda row: row[0]):
                if self.fast_permcheck or \
                        self._check_permission(req, name, 'view'):
                    resource = Resource(self.realm, name)
                    yield resource, set([tag[1] for tag in tags])

    def get_resource_tags(self, req, resource):
        assert resource.realm == self.realm
        ticket = Ticket(self.env, resource.id)
        if not self._check_permission(req, ticket.resource, 'view'):
            return
        return self._ticket_tags(ticket)

    def set_resource_tags(self, req, ticket_or_resource, tags, comment=u''):
        try:
            resource = ticket_or_resource.resource
        except AttributeError:
            resource = ticket_or_resource
            assert resource.realm == self.realm
            if not self._check_permission(req, resource, 'modify'):
                raise PermissionError(resource=resource, env=self.env)
            tag_set = set(tags)
            # Processing a call from TracTags, try to alter the ticket.
            tkt = Ticket(self.env, resource.id)
            all = self._ticket_tags(tkt)
            # Avoid unnecessary ticket changes, considering comments below.
            if tag_set != all:
                # Will only alter tags in 'keywords' ticket field.
                split_into_tags = TagSystem(self.env).split_into_tags
                keywords = split_into_tags(tkt['keywords'])
                # Assume, that duplication is depreciated and consolitation
                # wanted to primarily affect 'keywords' ticket field.
                # Consequently updating ticket tags and reducing (tag)
                # 'ticket_fields' afterwards may result in undesired tag loss.
                tag_set.difference_update(all.difference(keywords))
                tkt['keywords'] = u' '.join(sorted(map(to_unicode, tag_set)))
                tkt.save_changes(get_reporter_id(req), comment)
        else:
            # Processing a change listener event.
            tags = self._ticket_tags(ticket_or_resource)
            super(TicketTagProvider,
                  self).set_resource_tags(req, resource, tags)

    def remove_resource_tags(self, req, ticket_or_resource, comment=u''):
        try:
            resource = ticket_or_resource.resource
        except AttributeError:
            resource = ticket_or_resource
            assert resource.realm == self.realm
            if not self._check_permission(req, resource, 'modify'):
                raise PermissionError(resource=resource, env=self.env)
            # Processing a call from TracTags, try to alter the ticket.
            ticket = Ticket(self.env, resource.id)
            # Can only alter tags in 'keywords' ticket field.
            # DEVEL: Time to differentiate managed and sticky/unmanaged tags?
            ticket['keywords'] = u''
            ticket.save_changes(get_reporter_id(req), comment)
        else:
            # Processing a change listener event.
            super(TicketTagProvider, self).remove_resource_tags(req, resource)

    def describe_tagged_resource(self, req, resource):
        if not self.check_permission(req.perm, 'view'):
            return ''
        ticket = Ticket(self.env, resource.id)
        if ticket.exists:
            # Use the corresponding IResourceManager.
            ticket_system = TicketSystem(self.env)
            return ticket_system.get_resource_description(ticket.resource,
                                                          format='summary')
        else:
            return ''

    # ITicketChangeListener methods

    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        # Add any tags unconditionally.
        self.set_resource_tags(Mock(perm=MockPerm()), ticket, None)
        if self.use_cache:
            # Invalidate resource cache.
            del self._tagged_resources

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified."""
        # Sync only on change of ticket fields, that are exposed as tags.
        if any(f in self.fields for f in old_values.keys()):
            self.set_resource_tags(Mock(perm=MockPerm()), ticket, None)
            if self.use_cache:
                # Invalidate resource cache.
                del self._tagged_resources

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        self.remove_resource_tags(Mock(perm=MockPerm()), ticket)
        if self.use_cache:
            # Invalidate resource cache.
            del self._tagged_resources

    # Private methods

    def _fetch_tkt_tags(self):
        """Transfer all relevant ticket attributes to tags db table."""
        # Initial sync is done by forced, stupid one-way mirroring.
        # Data aquisition for this utilizes the known ticket tags query.
        db = self.env.get_db_cnx()
        fields = ["COALESCE(%s, '')" % f for f in self.fields]
        ignore = ''
        if self.ignore_closed_tickets:
            ignore = " WHERE status != 'closed'"
        sql = """
            SELECT *
              FROM (SELECT id, %s, %s AS std_fields
                      FROM ticket%s) s
            """ % (','.join(self.fields), db.concat(*fields), ignore)
        sql += " WHERE std_fields != '' ORDER BY id"
        self.env.log.debug(sql)
        # Obtain cursors for reading tickets and altering tags db table.
        # DEVEL: Use appropriate cursor typs from Trac 1.0 db API.
        ro_cursor = db.cursor()
        rw_cursor = db.cursor()
        # Delete all previous entries for 'ticket' tagspace.
        rw_cursor.execute('DELETE FROM tags WHERE tagspace=%s', (self.realm,))

        self.log.debug('ENTER_TAG_DB_CHECKOUT')
        ro_cursor.execute(sql)
        self.log.debug('EXIT_TAG_DB_CHECKOUT')
        split_into_tags = TagSystem(self.env).split_into_tags
        self.log.debug('ENTER_TAG_SYNC')

        for row in ro_cursor:
            tkt_id, ttags = row[0], ' '.join([f for f in row[1:-1] if f])
            ticket_tags = split_into_tags(ttags)
            rw_cursor.executemany("""
                INSERT INTO tags
                       (tagspace, name, tag)
                VALUES (%s, %s, %s)
                """, [(self.realm, str(tkt_id), tag) for tag in ticket_tags])
        db.commit()
        self.log.debug('EXIT_TAG_SYNC')

    try:
        from trac.cache import cached
        use_cache = True

        @cached
        def _tagged_resources(self, db=None):
            """Cached version."""
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            sql = """
                SELECT name, tag
                  FROM tags
                 WHERE tagspace=%s
                 ORDER by name
            """
            self.log.debug('ENTER_TAG_DB_CHECKOUT')
            cursor.execute(sql, (self.realm,))
            self.log.debug('EXIT_TAG_DB_CHECKOUT')

            resources = []
            self.log.debug('ENTER_TAG_GRID_MAKER')
            counter = 0
            for name, tags in groupby(cursor, lambda row: row[0]):
                resource = Resource(self.realm, name)
                resources.append((resource, set([tag[1] for tag in tags])))
                counter += 1
            self.log.debug('TAG_GRID_COUNTER: ' + str(counter))
            self.log.debug('EXIT_TAG_GRID_MAKER')
            return resources

    except ImportError:
        @property
        def _tagged_resources(self, db=None):
            """The old, uncached method."""
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            sql = """
                SELECT name, tag
                  FROM tags
                 WHERE tagspace=%s
                 ORDER by name
            """
            self.log.debug('ENTER_PER_REQ_TAG_DB_CHECKOUT')
            cursor.execute(sql, (self.realm,))
            self.log.debug('EXIT_PER_REQ_TAG_DB_CHECKOUT')

            self.log.debug('ENTER_TAG_GRID_MAKER_UNCACHED')
            for name, tags in groupby(cursor, lambda row: row[0]):
                resource = Resource(self.realm, name)
                yield resource, set([tag[1] for tag in tags])
            self.log.debug('EXIT_TAG_GRID_MAKER_UNCACHED')

    def _ticket_tags(self, ticket):
        split_into_tags = TagSystem(self.env).split_into_tags
        return split_into_tags(
            ' '.join(filter(None, [ticket[f] for f in self.fields])))
