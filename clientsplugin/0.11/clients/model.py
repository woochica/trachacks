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
            cursor.execute("SELECT description FROM client "
                           "WHERE name=%s", (name,))
            row = cursor.fetchone()
            if not row:
                raise TracError('Client %s does not exist.' % name)
            self.name = self._old_name = name
            #self.owner = row[0] or None
            self.description = row[0] or ''
        else:
            self.name = self._old_name = None
            #self.owner = None
            self.description = None

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
        cursor.execute("INSERT INTO client (name,description) "
                       "VALUES (%s,%s)",
                       (self.name, self.description))

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
        cursor.execute("UPDATE client SET name=%s,description=%s "
                       "WHERE name=%s",
                       (self.name, self.description,
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
        cursor.execute("SELECT name,description FROM client "
                       "ORDER BY name")
        for name, description in cursor:
            client = cls(env)
            client.name = client._old_name = name
            #client.owner = owner or None
            client.description = description or ''
            yield client
    select = classmethod(select)
