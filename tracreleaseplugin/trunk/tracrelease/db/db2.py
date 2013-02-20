# -*- coding: utf-8 -*-
# Copyright (C) 2008-2013 Joao Alexandre de Toledo <tracrelease@toledosp.com.br>
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.db import Table, Column, Index, DatabaseManager

tables = [
  Table('install_procedures', key = 'id')[
    Column('id', type = 'integer', auto_increment = True),
    Column('name'),
    Column('description'),
    Column('contain_files', type = 'integer')
  ],
  Table('release_installs')[
    Column('release_id', type = 'integer'),
    Column('install_id', type = 'integer')
  ],
  Table('release_files')[
    Column('release_id', type = 'integer'),
    Column('install_id', type = 'integer'),
    Column('file_order', type = 'integer'),
    Column('file_name')
  ]
]

def do_upgrade(env, cursor):
    db_connector, _ = DatabaseManager(env)._get_connector()

    # Create tables
    for table in tables:
        for statement in db_connector.to_sql(table):
            cursor.execute(statement)

    # Set database schema version.    
    cursor.execute("UPDATE system SET value = '2' WHERE name = 'release_version'")
