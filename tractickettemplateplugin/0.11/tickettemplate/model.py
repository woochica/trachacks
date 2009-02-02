# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         model.py
# Purpose:      The ticket template Trac plugin db model module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

"""Model classes for objects persisted in the database."""

import time

from trac.db import Table, Column, Index

class TT_Template(object):
    """Represents a generated tt."""

    _schema = [
        Table('tt_template', key='id')[
            Column('id', auto_increment=True), 
            Column('modi_time', type='int'),
            Column('tt_name'), 
            Column('tt_text'),
            Index(['tt_name', 'modi_time'])
        ],
        Table('tt_custom')[
            Column('username'),
            Column('tt_name'), 
            Column('tt_text'),
            Index(['username', 'tt_name'])
        ],
    ]

    def __init__(self, env, modi_time=None, tt_name=None, tt_text=None):
        """Initialize a new report with the specified attributes.

        To actually create this build log in the database, the `insert` method
        needs to be called.
        """
        self.env = env
        self.id = None
        self.modi_time = modi_time
        self.tt_name = tt_name
        self.tt_text = tt_text

    exists = property(fget=lambda self: self.id is not None,
                      doc='Whether this tt exists in the database')

#    def delete(self, db=None):
#        """Remove the tt from the database."""
#        assert self.exists, 'Cannot delete a non-existing report'
#        if not db:
#            db = self.env.get_db_cnx()
#            handle_ta = True
#        else:
#            handle_ta = False
#
#        cursor = db.cursor()
#        cursor.execute("DELETE FROM tt_template WHERE id=%s", (self.id,))
#
#        if handle_ta:
#            db.commit()
#        self.id = None

    def insert(cls, env, tt_name, tt_text, modi_time, db=None):
        """Insert a new tt into the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
            
        #modi_time = int(time.time())
        cursor = db.cursor()
        cursor.execute("INSERT INTO tt_template "
                       "(modi_time,tt_name,tt_text) VALUES (%s,%s,%s)",
                       (modi_time, tt_name, tt_text))
        id = db.get_last_id(cursor, 'tt_template')

        if handle_ta:
            db.commit()
        
        return id
    
    insert = classmethod(insert)
    
    def fetch(cls, env, tt_name, db=None):
        """Retrieve an existing tt from the database by ID."""
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()
        
        cursor.execute("SELECT tt_text FROM tt_template WHERE id="
                       "(SELECT max(id) FROM tt_template WHERE tt_name=%s)", (tt_name,))
        
        row = cursor.fetchone()
        if not row:
            return None
        else:
            return row[0]

    fetch = classmethod(fetch)

    def fetchById(cls, env, id, db=None):
        """Retrieve from the database that match
        the specified criteria.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT tt_text "
                       "FROM tt_template "
                       "WHERE id=%s", (id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        else:
            return row[0]
    
    fetchById = classmethod(fetchById)

    def getNameById(cls, env, id, db=None):
        """Retrieve from the database that match
        the specified criteria.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT tt_name "
                       "FROM tt_template "
                       "WHERE id=%s", (id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        else:
            return row[0]
    
    getNameById = classmethod(getNameById)


    def selectByName(cls, env, tt_name, db=None):
        """Retrieve from the database that match
        the specified criteria.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT id,modi_time,tt_name,tt_text "
                       "FROM tt_template "
                       "WHERE tt_name=%s ORDER BY modi_time DESC", (tt_name,))
        
        for id,modi_time,tt_name,tt_text in cursor:
            yield id,modi_time,tt_name,tt_text

    selectByName = classmethod(selectByName)

    def getCustomTemplate(cls, env, username, db=None):
        """Retrieve from the database that match
        the specified criteria.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT tt_name,tt_text "
                       "FROM tt_custom "
                       "WHERE username=%s ORDER BY tt_name ", (username,))
        
        return cursor.fetchall()

    getCustomTemplate = classmethod(getCustomTemplate)

    def saveCustom(cls, env, username, tt_name, tt_text, db=None):
        """Insert a new tt custom into the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
            
        cursor = db.cursor()

        # remove exist rows
        cursor.execute("DELETE FROM tt_custom WHERE username=%s AND tt_name=%s ;", (username, tt_name))
        
        cursor.execute("INSERT INTO tt_custom "
                       "(username,tt_name,tt_text) VALUES (%s,%s,%s)",
                       (username, tt_name, tt_text))

        if handle_ta:
            db.commit()
        
    
    saveCustom = classmethod(saveCustom)


    def deleteCustom(cls, env, username, tt_name, db=None):
        """Remove the custom from the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        cursor.execute("DELETE FROM tt_custom WHERE username='%s' AND tt_name='%s' ;" % (username, tt_name))

        if handle_ta:
            db.commit()

    deleteCustom = classmethod(deleteCustom)



schema = TT_Template._schema
schema_version = 3
