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

__all__ = ['Job','Run']

def simplify_whitespace(id):
    """Strip spaces and remove duplicate spaces within names"""
    return ' '.join(id.split())

class HTML(object):
    def __init__(self, **kwa):
        for k,v in kwa.items():
            setattr(self, k, v)
    
class Record(object):
    
    def __init__(self, env, **kwa):
        self._html = None
        self.env = env
        id = kwa.get('id')
        db= kwa.get('db')
        if  id:
             id = simplify_whitespace(id)
        if  id:
            if not db:
                db = self.env.get_db_cnx()
            cursor = db.cursor()
            sql =self.GET_SQL % ','.join(self.FIELDS)
            self.execute(cursor, sql,  ( id,))
            
            row = cursor.fetchone()
            if not row:
                raise TracError('%s %s does not exist.' % (self.__class__.__name__, id))
            self.setvaluesFromList(row)
            self.id = self._old_id =  id
        else:
            id = self.nextid(db)
            self.setvaluesFromList([None]*len(self.FIELDS))
            self.id = id
            self._old_id =  None
        
    def nextid(self, db): pass
        
    exists = property(fget=lambda self: self._old_id is not None)
    
    def delete(self, db=None):
        assert self.exists, 'Cannot deleting non-existent %s' % self.__class__.__name__
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
        cursor = db.cursor()
        self.env.log.info('Deleting %s %s'  % (self.__class__.__name__, id))
        self.execute(cursor, sql,   (self.id,))
        self.id = self._old_id = None
        if handle_ta:
            db.commit()
    
    
    def insert(self, db=None):
        name = self.__class__.__name__
        assert not self.exists, 'Cannot insert existing %s' % name
        self.id = simplify_whitespace(self.id)
        assert self.id, 'Cannot create %s without an id' % name
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
        cursor = db.cursor()
        self.env.log.debug("Creating new %s '%s'" % (name, self.id))
        sql = self.INSERT_SQL % (','.join(self.FIELDS), ','.join([ '%s']  * len(self.FIELDS)))
        self.execute(cursor, sql,  self.values)
        if handle_ta:
            db.commit()
    
    def update(self, db=None):
        assert self.exists, 'Cannot update non-existent %s' % self.__class__.__name__
        self.id = simplify_whitespace(self.id)
        assert self.id, 'Cannot update  %s with no id' % self.__class__.__name__
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        self.env.log.info('Updating %s "%s"' % (self.__class__.__name__, self.id))
        sql = self.UPDATE_SQL % ','.join([("%s=%%s" % k) for k in self.FIELDS])
        self.execute(cursor, sql, self.values+(self.id,))
        if self.id != self._old_id:
            self.cascade(self.id, self._old_id, db)
            self._old_id = self.id
        if handle_ta:
            db.commit()
    
    def select(cls, env, db=None):
        if not db:
            db = env.get_db_cnx()
        cursor = db.cursor()
        sql = cls.SELECT_SQL % ','.join(cls.FIELDS)
        cls.execute(cursor, sql)
        for row in cursor:
            obj = cls(env)
            obj.setvaluesFromList(row)
            obj._old_id = obj.id
            yield obj
    select = classmethod(select)
    

        
    def processValues(self, fields, values):
        return tuple(values)
        
    def _values(self):
        return self.processValues(self.FIELDS, [getattr(self, k) for k in self.FIELDS])
    values = property(_values)
    
    def setvaluesFromList(self, record):
        for i,(k, d) in enumerate(zip(self.FIELDS, self.defaults())):
                setattr(self, k, record[i] or d)
                
    def setvaluesFromDict(self, record, keys=None):
        if keys is None:
            keys = self.FIELDS
        for i,(k, d) in enumerate(zip(self.FIELDS, self.defaults())):
                if k in keys:
                    setattr(self, k, record.get(k, d))
    @classmethod
    def execute(self, cursor, sql, *args):
        print sql, args 
        return cursor.execute(sql, *args)
        
        
    def gethtml(self):
        self._html = self.forHtml(HTML(**vars(self)))
        return self._html
    html = property(gethtml) 

    
    
class Job(Record):
    GET_SQL    =    "SELECT %s FROM job WHERE id=%%s"
    DELETE_SQL =    "DELETE FROM job WHERE id=%s"
    INSERT_SQL =    "INSERT INTO job (%s) VALUES (%s)"
    UPDATE_SQL =    "UPDATE job SET %s WHERE id=%%s"
    SELECT_SQL =    "SELECT %s FROM job ORDER BY id"
    FIELDS    ='id','command','enabled'
    
    def __init__(self, env, **kwa):
        super(Job, self).__init__(env, **kwa)
        self.started = time.time()
        self.log = '
        
    def defaults(self):
        return  '',  '', True
    
   
class Run(Record):
    GET_SQL    =    "SELECT %s FROM run WHERE id=%%s"
    DELETE_SQL =    "DELETE FROM run WHERE id=%s"
    INSERT_SQL =    "INSERT INTO run (%s) VALUES (%s)"
    UPDATE_SQL =    "UPDATE run SET %s WHERE id=%%s"
    SELECT_BYJOB_SQL =    "SELECT %s FROM run where job=%%s ORDER BY id"  
    NEXT_ID =    "SELECT count(id) FROM run"  
    
    FIELDS  = 'id', 'job',  'started',  'ended', 'status', 'logpost','pid', 'uid', 'host', 'root', 'log'
    def defaults(self):
        for k,v in vars(self.env).items():
            print k, v
        return None, None,  time.time(),  0, 'STARTED', '','', '', '', '', ''
        
    def forHtml(self, html):
        html.started = self.started and time.ctime(self.started) or ''
        html.ended = self.ended and time.ctime(self.ended) or ''
        return html
    
    def nextid(self, db):
        if not db:
                db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql =self.NEXT_ID
        self.execute(cursor, sql)
        row = cursor.fetchone()
        print row
        return str(row[0]+1)
            
    def selectByJob(cls,  env, job, db=None):
        if not db:
            db = env.get_db_cnx()
        cursor = db.cursor()
        sql = cls.SELECT_BYJOB_SQL % ','.join(cls.FIELDS)
        cursor.execute(sql, (job,))
        for row in cursor:
            obj = cls(env)
            obj.setvaluesFromList(row)
            obj._old_id = obj.id
            yield obj
    selectByJob = classmethod(selectByJob)

    