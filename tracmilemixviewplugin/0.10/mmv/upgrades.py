# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         upgrades.py
# Purpose:      The MMV admin Trac plugin upgrade module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------


"""Automated upgrades for the MMV database tables, and other data stored
in the Trac environment."""

import os
import sys
import time

global ENV

def add_mmv_table(env, db):
    """Migrate db."""

    from model import schema
    from trac.db import DatabaseManager

    # Create the required tables
    db = env.get_db_cnx()
    connector, _ = DatabaseManager(env)._get_connector()
    cursor = db.cursor()
    for table in schema:
        for stmt in connector.to_sql(table):
            if table.name == "mmv_list":
                cursor.execute("ALTER TABLE mmv_list ADD COLUMN enabled INTEGER;")
            else:
                cursor.execute(stmt)

    db.commit()
    
map = {
    2: [add_mmv_table],
}
