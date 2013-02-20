# -*- coding: utf-8 -*-
# Copyright (C) 2008-2013 Joao Alexandre de Toledo <tracrelease@toledosp.com.br>
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.db import Table, Column, Index, DatabaseManager

tables = [
  Table('releases', key = 'id')[
    Column('id', type = 'integer', auto_increment = True),
    Column('version'),
    Column('description'),
    Column('author'),
    Column('creation_date', type = 'integer'),
    Column('planned_date', type = 'integer'),
    Column('install_date', type = 'integer')
  ],
  Table('release_tickets')[
    Column('release_id', type = 'integer'),
    Column('ticket_id', type = 'integer')
  ],
  Table('release_signatures')[
    Column('release_id', type = 'integer'),
    Column('signature'),
    Column('sign_date', type = 'integer')
  ]
]

def do_upgrade(env, cursor):
    db_connector, _ = DatabaseManager(env)._get_connector()

    # Create tables
    for table in tables:
        for statement in db_connector.to_sql(table):
            cursor.execute(statement)

    # Set database schema version.
    cursor.execute("INSERT INTO system (name, value) VALUES"
      " ('release_version', '1')")
