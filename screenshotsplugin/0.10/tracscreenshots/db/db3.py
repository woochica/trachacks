from trac.core import *
from trac.db import Table, Column, Index, DatabaseManager

tables = [
  Table('screenshot', key = 'id')
  [
    Column('id', type = 'integer', auto_increment = True),
    Column('name'),
    Column('description'),
    Column('time', type = 'integer'),
    Column('author'),
    Column('tags'),
    Column('file'),
    Column('width', type = 'integer'),
    Column('height', type = 'integer')
  ],
  Table('screenshot_component', key = 'id')
  [
     Column('id', type = 'integer', auto_increment = True),
     Column('screenshot', type = 'integer'),
     Column('component')
  ],
  Table('screenshot_version', key = 'id')
  [
    Column('id', type = 'integer', auto_increment = True),
    Column('screenshot', type = 'integer'),
    Column('version')
  ]
]

def do_upgrade(env, cursor, incremental):
    db_connector, _ = DatabaseManager(env)._get_connector()

    if incremental:
        raise TracError("Incremental upgrade not supported yet.")

    # Create new tables
    for table in tables:
        for statement in db_connector.to_sql(table):
            cursor.execute(statement)

    # Set database schema version.
    if incremental:
        cursor.execute("UPDATE system SET value = '3' WHERE name = "
          "'screenshots_version'")
    else:
        cursor.execute("INSERT INTO system (name, value) VALUES "
          "('screenshots_version', '3')")