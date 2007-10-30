import re
import sys
import time
from datetime import date, datetime

from trac.attachment import Attachment
from trac.context import ResourceNotFound
from trac.core import TracError
from trac.ticket.api import TicketSystem
from trac.util import sorted, embedded_numbers
from trac.util.datefmt import utc, utcmax, to_timestamp

__all__ = ['Client']

def simplify_whitespace(name):
    """Strip spaces and remove duplicate spaces within names"""
    return ' '.join(name.split())

class Client(object):

    def __init__(self, env, name=None, db=None):
        self.env = env
        if name:
            name = simplify_whitespace(name)
        if name:
            if not db:
                db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT description,"
                           "changes_list, changes_period, changes_lastupdate,"
                           "summary_list, summary_period, summary_lastupdate,"
                           "default_rate, currency "
                           "FROM client "
                           "WHERE name=%s", (name,))
            row = cursor.fetchone()
            if not row:
                raise TracError('Client %s does not exist.' % name)
            self.name = self._old_name = name
            self.description = row[0] or ''
            self.changes_list = row[1] or ''
            self.changes_period = row[2] or 'never'
            self.changes_lastupdate = row[3] or 0
            self.summary_list = row[4] or ''
            self.summary_period = row[5] or 'never'
            self.summary_lastupdate = row[6] or 0
            self.default_rate = row[7] or ''
            self.currency = row[8] or ''
        else:
            self.name = self._old_name = None
            self.description = None
            self.changes_list = ''
            self.changes_period = 'never'
            self.changes_lastupdate = 0
            self.summary_list = ''
            self.summary_period = 'never'
            self.summary_lastupdate = 0
            self.default_rate = ''
            self.currency = ''

    exists = property(fget=lambda self: self._old_name is not None)

    def delete(self, db=None):
        assert self.exists, 'Cannot deleting non-existent client'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        self.env.log.info('Deleting client %s' % self.name)
        cursor.execute("DELETE FROM client WHERE name=%s", (self.name,))

        self.name = self._old_name = None

        if handle_ta:
            db.commit()

    def insert(self, db=None):
        assert not self.exists, 'Cannot insert existing client'
        self.name = simplify_whitespace(self.name)
        assert self.name, 'Cannot create client with no name'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        self.env.log.debug("Creating new client '%s'" % self.name)
        cursor.execute("INSERT INTO client (name,description,"
                       " changes_list, changes_period, changes_lastupdate,"
                       " summary_list, summary_period, summary_lastupdate,"
                       " default_rate, currency) "
                       "VALUES (%s,%s, %s,%s,%s, %s,%s,%s, %s,%s)",
                       (self.name, self.description,
                        self.changes_list, self.changes_period, int(time.time()),
                        self.summary_list, self.summary_period, int(time.time()),
                        self.default_rate, self.currency))

        if handle_ta:
            db.commit()

    def update(self, db=None):
        assert self.exists, 'Cannot update non-existent client'
        self.name = simplify_whitespace(self.name)
        assert self.name, 'Cannot update client with no name'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        self.env.log.info('Updating client "%s"' % self.name)
        cursor.execute("UPDATE client SET name=%s,description=%s,"
                       " changes_list=%s, changes_period=%s,"
                       " summary_list=%s, summary_period=%s,"
                       " default_rate=%s, currency=%s "
                       "WHERE name=%s",
                       (self.name, self.description,
                        self.changes_list, self.changes_period,
                        self.summary_list, self.summary_period,
                        self.default_rate, self.currency,
                        self._old_name))
        if self.name != self._old_name:
            # Update tickets
            cursor.execute("UPDATE ticket_custom SET value=%s "
                           "WHERE name=%s AND value=%s",
                           (self.name, 'client', self._old_name))
            self._old_name = self.name

        if handle_ta:
            db.commit()

    def select(cls, env, db=None):
        if not db:
            db = env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT name,description,"
                       " changes_list, changes_period, changes_lastupdate,"
                       " summary_list, summary_period, summary_lastupdate,"
                       " default_rate, currency "
                       "FROM client "
                       "ORDER BY name")
        for name, description, changes_list, changes_period, changes_lastupdate, summary_list, summary_period, summary_lastupdate, default_rate, currency in cursor:
            client = cls(env)
            client.name = client._old_name = name
            client.description = description or ''
            client.changes_list = changes_list or ''
            client.changes_period = changes_period or 'never'
            client.changes_lastupdate = changes_lastupdate or 0
            client.summary_list = summary_list or ''
            client.summary_period = summary_period or 'never'
            client.summary_lastupdate = summary_lastupdate or 0
            client.default_rate = default_rate or ''
            client.currency = currency or ''
            yield client
    select = classmethod(select)
