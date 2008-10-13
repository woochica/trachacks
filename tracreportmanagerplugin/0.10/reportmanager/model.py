# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         model.py
# Purpose:      The report manager Trac plugin db model module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

"""Model classes for objects persisted in the database."""

import time

from trac.db import Table, Column, Index

class ReportHistory(object):
    """Represents the history of reports."""

    _schema = [
        Table('reports_history', key='id')[
            Column('id', auto_increment=True), Column('save_time', type='int'),
            Column('reports_log'), Column('reports_content'),
            Index(['reports_log', 'save_time'])
        ]
    ]

    def __init__(self, env, save_time=None, reports_log=None, reports_content=None):
        """Initialize a new reports entry with the specified attributes.
        """
        self.env = env
        self.id = None
        self.save_time = save_time
        self.reports_log = reports_log
        self.reports_content = reports_content

    exists = property(fget=lambda self: self.id is not None,
                      doc='Whether this reports entry exists in the database')

    def delete(cls, env, id, db=None):
        """Remove the reports entry from the database."""
        #assert self.exists, 'Cannot delete a non-existing reports hostory'
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
            
        cursor = db.cursor()
        cursor.execute("DELETE FROM reports_history WHERE id=%s", (id,))

        if handle_ta:
            db.commit()

    delete = classmethod(delete)


    def insert(cls, env, reports_log, reports_content, save_time, db=None):
        """Insert a new reports entry into the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
            
        cursor = db.cursor()
        cursor.execute("INSERT INTO reports_history "
                       "(save_time,reports_log,reports_content) VALUES (%s,%s,%s)",
                       (save_time, reports_log, reports_content))
        id = db.get_last_id(cursor, 'reports_history')

        if handle_ta:
            db.commit()
        
        return id
    
    insert = classmethod(insert)
    
    def fetchLast(cls, env, save_time, db=None):
        """Retrieve the latest reports entry."""
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()
        
        cursor.execute("SELECT reports_content FROM reports_history WHERE id="
                       "(SELECT max(id) FROM reports_history)")
        
        row = cursor.fetchone()
        if not row:
            return None
        else:
            return row[0]

    fetchLast = classmethod(fetchLast)

    def fetchById(cls, env, id, db=None):
        """Retrieve from the database by id.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT reports_content "
                       "FROM reports_history "
                       "WHERE id=%s", (id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        else:
            return row[0]
    
    fetchById = classmethod(fetchById)

    def getLogById(cls, env, id, db=None):
        """Retrieve reports log from the database by id.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT reports_log "
                       "FROM reports_history "
                       "WHERE id=%s", (id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        else:
            return row[0]
    
    getLogById = classmethod(getLogById)

    def getReportsHistory(cls, env, db=None):
        """Retrieve reports history.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT id, save_time, reports_log, reports_content "
                       "FROM reports_history "
                       "ORDER BY id")
        
        return cursor.fetchall()
    
    getReportsHistory = classmethod(getReportsHistory)



schema = ReportHistory._schema
schema_version = 1
