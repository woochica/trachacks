# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2012 Noah Kantrowitz <noah@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import copy
from datetime import datetime

from trac.ticket.model import Ticket
from trac.util.compat import set, sorted
from trac.util.datefmt import utc, to_utimestamp


class TicketLinks(object):
    """A model for the ticket links used MasterTickets."""

    def __init__(self, env, tkt, db=None):
        self.env = env
        if not isinstance(tkt, Ticket):
            tkt = Ticket(self.env, tkt)
        self.tkt = tkt

        db = db or self.env.get_db_cnx()
        cursor = db.cursor()

        cursor.execute('SELECT dest FROM mastertickets WHERE source=%s ORDER BY dest', (self.tkt.id,))
        self.blocking = set([int(num) for num, in cursor])
        self._old_blocking = copy.copy(self.blocking)

        cursor.execute('SELECT source FROM mastertickets WHERE dest=%s ORDER BY source', (self.tkt.id,))
        self.blocked_by = set([int(num) for num, in cursor])
        self._old_blocked_by = copy.copy(self.blocked_by)

    def save(self, author, comment='', when=None, db=None):
        """Save new links."""
        if when is None:
            when = datetime.now(utc)
        when_ts = to_utimestamp(when)

        handle_commit = False
        if db is None:
            db = self.env.get_db_cnx()
            handle_commit = True
        cursor = db.cursor()

        new_blocking = set(int(n) for n in self.blocking)
        new_blocked_by = set(int(n) for n in self.blocked_by)

        to_check = [
            # new, old, field
            (new_blocking, self._old_blocking, 'blockedby', ('source', 'dest')),
            (new_blocked_by, self._old_blocked_by, 'blocking', ('dest', 'source')),
        ]

        for new_ids, old_ids, field, sourcedest in to_check:
            for n in new_ids | old_ids:
                update_field = None
                if n in new_ids and n not in old_ids:
                    # New ticket added
                    cursor.execute('INSERT INTO mastertickets (%s, %s) VALUES (%%s, %%s)' % sourcedest,
                                   (self.tkt.id, n))
                    update_field = lambda lst: lst.append(str(self.tkt.id))
                elif n not in new_ids and n in old_ids:
                    # Old ticket removed
                    cursor.execute('DELETE FROM mastertickets WHERE %s=%%s AND %s=%%s' % sourcedest, (self.tkt.id, n))
                    update_field = lambda lst: lst.remove(str(self.tkt.id))

                if update_field is not None:
                    cursor.execute('SELECT value FROM ticket_custom WHERE ticket=%s AND name=%s',
                                   (n, str(field)))
                    old_value = (cursor.fetchone() or ('',))[0]
                    new_value = [x.strip() for x in old_value.split(',') if x.strip()]
                    update_field(new_value)
                    new_value = ', '.join(sorted(new_value, key=lambda x: int(x)))

                    # ticket, time and field must be unique for database integrity
                    # The TicketImportPlugin assigns the same changetime to all ticket
                    # if not specified, which was causing an IntegrityError (#10194).
                    changelog = Ticket(self.env, n).get_changelog(when=when)
                    if any(field in cl for cl in changelog):
                        cursor.execute("""
                            UPDATE ticket_change SET author=%s,
                              oldvalue=%s, newvalue=%s
                            WHERE ticket=%s AND time=%s AND field=%s
                            """, (author, old_value, new_value, n,
                                  when_ts, field)
                        )
                    else:
                        cursor.execute("""
                            INSERT INTO ticket_change (ticket, time, author,
                              field, oldvalue, newvalue)
                            VALUES (%s, %s, %s, %s, %s, %s)""",
                                (n, when_ts, author, field, old_value, new_value)
                        )

                    # Add comment to referenced ticket if a comment hasn't already been added
                    if comment and not any('comment' in entry for entry in self.tkt.get_changelog(when)):
                        cursor.execute(
                            'INSERT INTO ticket_change (ticket, time, author, field, oldvalue, newvalue) VALUES (%s, %s, %s, %s, %s, %s)',
                            (n, when_ts, author, 'comment', '', '(In #%s) %s' % (self.tkt.id, comment)))

                    cursor.execute('UPDATE ticket_custom SET value=%s WHERE ticket=%s AND name=%s',
                                   (new_value, n, field))

                    # refresh the changetime to prevent concurrent edits
                    cursor.execute('UPDATE ticket SET changetime=%s WHERE id=%s', (when_ts, n))

                    if not cursor.rowcount:
                        cursor.execute('INSERT INTO ticket_custom (ticket, name, value) VALUES (%s, %s, %s)',
                                       (n, field, new_value))

        # cursor.execute('DELETE FROM mastertickets WHERE source=%s OR dest=%s', (self.tkt.id, self.tkt.id))
        # data = []
        # for tkt in self.blocking:
        #     if isinstance(tkt, Ticket):
        #         tkt = tkt.id
        #     data.append((self.tkt.id, tkt))
        # for tkt in self.blocked_by:
        #     if isisntance(tkt, Ticket):
        #         tkt = tkt.id
        #     data.append((tkt, self.tkt.id))
        # 
        # cursor.executemany('INSERT INTO mastertickets (source, dest) VALUES (%s, %s)', data)

        if handle_commit:
            db.commit()

    def __nonzero__(self):
        return bool(self.blocking) or bool(self.blocked_by)

    def __repr__(self):
        def l(arr):
            arr2 = []
            for tkt in arr:
                if isinstance(tkt, Ticket):
                    tkt = tkt.id
                arr2.append(str(tkt))
            return '[%s]' % ','.join(arr2)

        return '<mastertickets.model.TicketLinks #%s blocking=%s blocked_by=%s>' % \
               (self.tkt.id, l(getattr(self, 'blocking', [])), l(getattr(self, 'blocked_by', [])))

    @staticmethod
    def walk_tickets(env, tkt_ids, full=False):
        """Return an iterable of all links reachable directly above or below those ones."""

        def visit(tkt, memo, next_fn, full=False):
            if tkt in memo:
                return False

            links = TicketLinks(env, tkt)
            memo[tkt] = links

            for n in next_fn(links):
                visit(n, memo, next_fn)

        memo1 = {}
        memo2 = {}
        for id in tkt_ids:
            if full:
                visit(id, memo1, lambda links: links.blocking | links.blocked_by)
            else:
                visit(id, memo1, lambda links: links.blocking)
                visit(id, memo2, lambda links: links.blocked_by)
        memo1.update(memo2)
        return memo1.itervalues()
