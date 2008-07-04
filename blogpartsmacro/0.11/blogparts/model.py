# -*- coding: utf-8 -*-


import re
import sys
import time
from datetime import date, datetime

from trac.attachment import Attachment
from trac.core import TracError
from trac.resource import Resource, ResourceNotFound
from trac.ticket.api import TicketSystem
from trac.util import sorted, embedded_numbers
from trac.util.datefmt import utc, utcmax, to_timestamp
from trac.util.translation import _

__all__ = ['BlogPart']

class BlogPart(object):

    def __init__(self, env, name=None, db=None):
        self.env = env
        if name:
            if not db:
                db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT time,description,summery,header,body,argnum FROM blogpart "
                           "WHERE name=%s", (name,))
            row = cursor.fetchone()
            if not row:
                raise ResourceNotFound(_('BlogPart %(name)s does not exist.',
                                  name=name))
            self.name = self._old_name = name
            self.time = row[0] and datetime.fromtimestamp(int(row[0]), utc) or None
            self.description = row[1] or ''
            self.summery = row[2] or ''
            self.header = row[3] or ''
            self.body = row[4] or ''
            self.argnum = row[5] or 0
        else:
            self.name = self._old_name = None
            self.time = None
            self.description = None
            self.summery = None
            self.header = None
            self.body = None
            self.argnum = None

    exists = property(fget=lambda self: self._old_name is not None)

    def delete(self, db=None):
        assert self.exists, 'Cannot delete non-existent blogpart'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        self.env.log.info('Deleting blogpart %s' % self.name)
        cursor.execute("DELETE FROM blogpart WHERE name=%s", (self.name,))

        self.name = self._old_name = None

        if handle_ta:
            db.commit()

    def insert(self, db=None):
        assert not self.exists, 'Cannot insert existing blogpart'
        self.name = simplify_whitespace(self.name)
        assert self.name, 'Cannot create blogpart with no name'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        self.env.log.debug("Creating new blogpart '%s'" % self.name)
        cursor.execute("INSERT INTO blogpart (name,time,description,summery,header,body,argnum) "
                       "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                       (self.name, to_timestamp(self.time), self.description, 
                        self.summery,self.header,self.body,self.argnum))

        if handle_ta:
            db.commit()

    def update(self, db=None):
        assert self.exists, 'Cannot update non-existent blogpart'
        self.name = simplify_whitespace(self.name)
        assert self.name, 'Cannot update blogpart with no name'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        self.env.log.info('Updating blogpart "%s"' % self.name)
        cursor.execute("UPDATE blogpart SET name=%s,time=%s,description=%s,"
                       "summery=%s,header=%s,body=%s,argnum=%s "
                       "WHERE name=%s",
                       (self.name, to_timestamp(self.time), self.description,
                        self.summery,self.header,self.body,self.argnum,
                        self._old_name))

        if handle_ta:
            db.commit()

    def select(cls, env, db=None):
        if not db:
            db = env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT name,time,description,summery,header,body,argnum FROM blogpart")
        blogparts = []
        for name, time, description,summery,header,body,argnum in cursor:
            blogpart = cls(env)
            blogpart.name = blogpart._old_name = name
            blogpart.time = time and datetime.fromtimestamp(int(time), utc) or None
            blogpart.description = description or ''
            blogpart.summery = summery
            blogpart.header = header
            blogpart.blody = body
            blogpart.argnum = argnum
            blogparts.append(blogpart)
        def blogpart_order(v):
            return (v.time or utcmax, embedded_numbers(v.name))
        return sorted(blogparts, key=blogpart_order, reverse=True)
    select = classmethod(select)
    
def simplify_whitespace(name):
    """Strip spaces and remove duplicate spaces within names"""
    return ' '.join(name.split())
        
    