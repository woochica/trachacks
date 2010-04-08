# -*- coding: utf-8 -*-
import re
import sys
import time
from datetime import date, datetime

from trac.attachment import Attachment
from trac.core import TracError
from trac.ticket.api import TicketSystem
from trac.util import sorted, embedded_numbers
from trac.util.datefmt import utc, utcmax, to_timestamp

__all__ = ['Job']

def simplify_whitespace(name):
    """Strip spaces and remove duplicate spaces within names"""
    return ' '.join(name.split())

class Job(object):
    def __init__(self, env, jobid=None, db=None):
        self.env = env
        if jobid:
            jobid = simplify_whitespace(jobid)
        if jobid:
            if not db:
                db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT release, enabled FROM job WHERE id=%s", (jobid,))
            row = cursor.fetchone()
            if not row:
                raise TracError('Job %s does not exist.' % name)
            self.id = self._old_id = jobid
            self.release = row[0] or ''
            self.enabled = row[1] == 'True' 
        else:
            self.release =  ''
            self.enabled = False
        self.id = self._old_id = jobid
            
    exists = property(fget=lambda self: self._old_id is not None)

    def delete(self, db=None):
        assert self.exists, 'Cannot deleting non-existent job'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
        cursor = db.cursor()
        self.env.log.info('Deleting job %s' % self.id)
        cursor.execute("DELETE FROM job WHERE id=%s", (self.id,))
        self.id = self._old_id = None
        if handle_ta:
            db.commit()
    

    def enable(self, shouldEnable, db=None):
        assert self.exists, 'Cannot enable/diable non-existent job'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
        cursor = db.cursor()
        cursor.execute("UPDATE job SET enabled=%s WHERE id=%s", (shouldEnable, self.id,))
        if handle_ta:
            db.commit()

    

            

    def insert(self, db=None):
        assert not self.exists, 'Cannot insert existing job'
        self.id = simplify_whitespace(self.id)
        assert self.id, 'Cannot create job withou an id'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
        cursor = db.cursor()
        self.env.log.debug("Creating new job '%s'" % self.id)
        cursor.execute("INSERT INTO job (id, release, enabled) VALUES (%s,%s,%s)", (self.id, self.release, self.enabled))
        if handle_ta:
            db.commit()

    def update(self, db=None):
        assert self.exists, 'Cannot update non-existent job'
        self.id = simplify_whitespace(self.id)
        assert self.id, 'Cannot update job with no id'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        self.env.log.info('Updating job "%s"' % self.id)
        cursor.execute("UPDATE job SET id=%s, release=%s, enabled=%s WHERE id=%s", (self.id, self.release, self.enabled,self.id))
        if self.id != self._old_id:
            """
            # Update tickets
            cursor.execute("UPDATE ticket_custom SET value=%s "
                           "WHERE name=%s AND value=%s",
                           (self.id 'job', self._old_id))
            """
            # Update event options
            cursor.execute("UPDATE run SET job=%s WHERE job=%s",  (self.id, self._old_id))
            self._old_id = self.id

        if handle_ta:
            db.commit()

    def select(cls, env, db=None):
        if not db:
            db = env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT id, release, enabled FROM job ORDER BY id")
        for id, release, enabled in cursor:
            job = cls(env)
            job.id = job._old_id = id
            job.release = release or ''
            job.enabled = enabled == 'True'
            yield job
    select = classmethod(select)
