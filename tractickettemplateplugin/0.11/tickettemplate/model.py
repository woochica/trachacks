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

from utils import *


class TT_Template(object):
    """Represents a generated tt."""

    _schema = [
        Table('ticket_template_store')[
            Column('tt_time', type='int'),
            Column('tt_user'), 
            Column('tt_name'), 
            Column('tt_field'),
            Column('tt_value'),
        ]
    ]

    def __init__(self, env):
        """Initialize a new report with the specified attributes.

        To actually create this build log in the database, the `insert` method
        needs to be called.
        """
        self.env = env

    exists = property(fget=lambda self: self.id is not None,
                      doc='Whether this tt exists in the database')

    def deleteCustom(cls, env, data):
        """Remove the tt from the database."""
        db = env.get_db_cnx()
        cursor = db.cursor()
        sqlString = """DELETE FROM ticket_template_store 
                        WHERE tt_user=%s 
                        AND tt_name=%s
                    """
        cursor.execute(sqlString, (data["tt_user"], data["tt_name"], ))

        db.commit()
    deleteCustom = classmethod(deleteCustom)

    def insert(cls, env, record):
        """Insert a new tt into the database."""
        db = env.get_db_cnx()
            
        cursor = db.cursor()
        sqlString = """INSERT INTO ticket_template_store 
                       (tt_time,tt_user,tt_name,tt_field,tt_value) 
                       VALUES (%s,%s,%s,%s,%s)"""
        cursor.execute(sqlString, record)
        db.commit()
        
    insert = classmethod(insert)
    
    def fetchCurrent(cls, env, data):
        """Retrieve an existing tt from the database by ID."""
        db = env.get_db_cnx()

        cursor = db.cursor()
        sqlString = """SELECT tt_field, tt_value  
                        FROM ticket_template_store 
                        WHERE tt_user = %s
                        AND tt_time =  (SELECT max(tt_time) 
                            FROM ticket_template_store 
                            WHERE tt_name=%s)
                    """
        cursor.execute(sqlString, (data["tt_user"], data["tt_name"], ))
        
        field_value_mapping = {}
        for tt_field, tt_value in cursor.fetchall():
            if tt_value:
                field_value_mapping[tt_field] = tt_value

        return field_value_mapping

    fetchCurrent = classmethod(fetchCurrent)

    def fetchAll(cls, env, data):
        """Retrieve an existing tt from the database by ID.
            result:
                {
                    "field_value_mapping":{
                            "default":{
                                    "summary":"aaa",
                                    "description":"bbb",
                                },

                        },
                    "field_value_mapping_custom":{
                            "my_template":{
                                    "summary":"ccc",
                                    "description":"ddd",
                                },

                        },
                }

        """
        db = env.get_db_cnx()

        cursor = db.cursor()

        real_user = data.get("tt_user")
        req_args = data.get("req_args")

        field_value_mapping = {}
        field_value_mapping_custom = {}

        # field_value_mapping_custom
        sqlString = """SELECT tt_name, tt_field, tt_value 
                        FROM ticket_template_store 
                        WHERE tt_user = %s
                    """

        cursor.execute(sqlString, (data["tt_user"], ))
    
        for tt_name, tt_field, tt_value in cursor.fetchall():
            if not field_value_mapping_custom.has_key(tt_name):
                field_value_mapping_custom[tt_name] = {}
            if tt_value:
                tt_value = formatField(env.config, tt_value, real_user, req_args)
                field_value_mapping_custom[tt_name][tt_field] = tt_value


        # field_value_mapping
        sqlString = """SELECT DISTINCT tt_name 
                        FROM ticket_template_store
                        WHERE tt_user = %s
                    """
        cursor.execute(sqlString, (SYSTEM_USER, ))
        
        tt_name_list = [row[0] for row in cursor.fetchall()]

        data["tt_user"] = SYSTEM_USER
        for tt_name in tt_name_list:
            data["tt_name"] = tt_name

            sqlString = """SELECT tt_field, tt_value 
                            FROM ticket_template_store 
                            WHERE tt_user = %s 
                            AND tt_name = %s 
                            AND tt_time =  (SELECT max(tt_time) 
                                FROM ticket_template_store 
                                WHERE tt_name = %s)
                        """
            cursor.execute(sqlString, (data["tt_user"], data["tt_name"], data["tt_name"], ))
        
            for tt_field, tt_value in cursor.fetchall():
                if not field_value_mapping.has_key(tt_name):
                    field_value_mapping[tt_name] = {}
                if tt_value:
                    tt_value = formatField(env.config, tt_value, real_user, req_args)
                    field_value_mapping[tt_name][tt_field] = tt_value

        result = {}
        result["field_value_mapping"] = field_value_mapping
        result["field_value_mapping_custom"] = field_value_mapping_custom
        return result

    fetchAll = classmethod(fetchAll)

    def getCustomTemplate(cls, env, tt_user):
        """Retrieve from the database that match
        the specified criteria.
        """
        db = env.get_db_cnx()

        cursor = db.cursor()

        sqlString = """SELECT DISTINCT tt_name 
                       FROM ticket_template_store 
                       WHERE tt_user = %s 
                       ORDER BY tt_name 
                    """

        cursor.execute(sqlString, (tt_user, ))
        
        return [row[0] for row in cursor.fetchall()]

    getCustomTemplate = classmethod(getCustomTemplate)

    def fetch(cls, env, tt_name, db=None):
        """Retrieve an existing tt from the database by ID."""
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()
        sqlString = """SELECT tt_value 
                        FROM ticket_template_store 
                        WHERE tt_time=(
                            SELECT max(tt_time) 
                                FROM ticket_template_store 
                                WHERE tt_name=%s and tt_field='description'
                            )
                    """
        
        cursor.execute(sqlString, (tt_name,))
        
        row = cursor.fetchone()
        if not row:
            return None
        else:
            return row[0]

    fetch = classmethod(fetch)
    
schema = TT_Template._schema
schema_version = 4
