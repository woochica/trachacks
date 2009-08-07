# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         model.py
# Purpose:      The TracTicketChainedFields Trac plugin db model module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

"""Model classes for objects persisted in the database."""

import time

from trac.db import Table, Column, Index

class TracTicketChainedFields_List(object):
    """Represents a table."""

    _schema = [
        Table('tcf_list', key='id')[
            Column('id', auto_increment=True),
            Column('tcf_define'),
            Column('tcf_time', type='int'),
            Index(['id'])
        ]
    ]

    def __init__(self, env):
        """Initialize a new entry with the specified attributes.

        To actually create this build log in the database, the `insert` method
        needs to be called.
        """
        self.env = env

    # def delete(cls, env, col1, db=None):
        # """Remove the col1 from the database."""
        # if not db:
            # db = env.get_db_cnx()
            # handle_ta = True
        # else:
            # handle_ta = False

        # cursor = db.cursor()
        # cursor.execute("DELETE FROM tcf_list WHERE col1=%s;", (col1,))

        # if handle_ta:
            # db.commit()

    # delete = classmethod(delete)

    def insert(cls, env, tcf_define, db=None):
        """Insert a new col1 into the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
        
        tcf_time = int(time.time())
        cursor = db.cursor()
        cursor.execute("INSERT INTO tcf_list (tcf_define, tcf_time) VALUES (%s, %s)",
                       (tcf_define, tcf_time))

        if handle_ta:
            db.commit()

    insert = classmethod(insert)

    def get_tcf_define(cls, env, db=None):
        """Retrieve from the database that match
        the specified criteria.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT tcf_define FROM tcf_list ORDER BY tcf_time DESC LIMIT 1")
        
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            return ""

    get_tcf_define = classmethod(get_tcf_define)


schema = TracTicketChainedFields_List._schema
schema_version = 1