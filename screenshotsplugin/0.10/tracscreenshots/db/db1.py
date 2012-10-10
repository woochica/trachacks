# -*- coding: utf-8 -*-

from trac.db import Table, Column, Index, DatabaseManager

tables = [
  Table('screenshot', key = 'id')
  [
    Column('id', type = 'integer', auto_increment = True),
    Column('name'),
    Column('description'),
    Column('time', type = 'integer'),
    Column('author'),
    Column('large_file'),
    Column('medium_file'),
    Column('small_file'),
    Column('component'),
    Column('version')
  ]
]

def do_upgrade(env, cursor, incremental):
    db_connector, _ = DatabaseManager(env)._get_connector()

    # Create tables
    for table in tables:
        for statement in db_connector.to_sql(table):
            cursor.execute(statement)

    # Set database schema version.
    cursor.execute("INSERT INTO system (name, value) VALUES"
      " ('screenshots_version', '1')")
