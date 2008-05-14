# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         model.py
# Purpose:      The MileMixView admin Trac plugin db model module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

"""Model classes for objects persisted in the database."""

import time

from trac.db import Table, Column, Index

class RT_Template(object):
    """Represents a generated tt."""

    _schema = [
        Table('rt_template', key='id')[
            Column('id', auto_increment=True), 
            Column('milestone'), 
            Index(['milestone'])
        ]
    ]

    def __init__(self, env, milestone=None):
        """Initialize a new entry with the specified attributes.

        To actually create this build log in the database, the `insert` method
        needs to be called.
        """
        self.env = env
        self.id = None
        self.milestone = milestone

    def delete(cls, env, milestone, db=None):
        """Remove the milestone from the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        cursor.execute("DELETE FROM rt_template WHERE milestone=%s", (milestone,))

        if handle_ta:
            db.commit()

    delete = classmethod(delete)

    def deleteAll(cls, env, db=None):
        """Remove the milestone from the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        cursor.execute("DELETE FROM rt_template")

        if handle_ta:
            db.commit()

    deleteAll = classmethod(deleteAll)


    def insert(cls, env, milestone, db=None):
        """Insert a new milestone into the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
            
        cursor = db.cursor()
        cursor.execute("INSERT INTO rt_template "
                       "(milestone) VALUES (%s)",
                       (milestone,))
        id = db.get_last_id(cursor, 'rt_template')

        if handle_ta:
            db.commit()
        
        return id
    
    insert = classmethod(insert)
    
#    def fetch(cls, env, milestone, db=None):
#        """Retrieve an existing milestone from the database by ID."""
#        if not db:
#            db = env.get_db_cnx()
#
#        cursor = db.cursor()
#        
#        cursor.execute("SELECT tt_text FROM rt_template WHERE id="
#                       "(SELECT max(id) FROM rt_template WHERE tt_name=%s)", (tt_name,))
#        
#        row = cursor.fetchone()
#        if not row:
#            return None
#        else:
#            return row[0]
#
#    fetch = classmethod(fetch)

    def fetchById(cls, env, id, db=None):
        """Retrieve from the database that match
        the specified criteria.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT milestone "
                       "FROM rt_template "
                       "WHERE id=%s", (id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        else:
            return row[0]
    
    fetchById = classmethod(fetchById)

#    def getNameById(cls, env, id, db=None):
#        """Retrieve from the database that match
#        the specified criteria.
#        """
#        if not db:
#            db = env.get_db_cnx()
#
#        cursor = db.cursor()
#
#        cursor.execute("SELECT milestone "
#                       "FROM rt_template "
#                       "WHERE id=%s", (id,))
#        
#        row = cursor.fetchone()
#        if not row:
#            return None
#        else:
#            return row[0]
#    
#    getNameById = classmethod(getNameById)


    def getMilestones(cls, env, db=None):
        """Retrieve from the database that match
        the specified criteria.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT milestone "
                       "FROM rt_template")
        
        return [m[0] for m in cursor.fetchall()]

    getMilestones = classmethod(getMilestones)

schema = RT_Template._schema
schema_version = 1
