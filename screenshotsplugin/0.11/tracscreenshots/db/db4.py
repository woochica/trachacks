# -*- coding: utf-8 -*-

import os, Image

from trac.core import *
from trac.db import Table, Column, Index, DatabaseManager

from tracscreenshots.api import *

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
    Column('height', type = 'integer'),
    Column('priority', type = 'integer')
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

db_version = 4

def do_upgrade(env, cursor, incremental):
    db_connector, _ = DatabaseManager(env)._get_connector()

    # Create context and cursor.
    context = Context('screenshots-update')
    context.cursor = cursor

    # Access API component.
    api = env[ScreenshotsApi]

    if incremental:
        # Backup old screenshot table.
        cursor.execute("CREATE TEMPORARY TABLE screenshot_old AS SELECT * "
          "FROM screenshot")
        cursor.execute("DROP TABLE screenshot")

        # Create new screenshot table.
        for statement in db_connector.to_sql(tables[0]):
            cursor.execute(statement)

        # Get screenshots from old table.
        screenshots = api._get_items(context, 'screenshot_old', ('id', 'name',
          'description', 'time', 'author', 'tags', 'file', 'width', 'height'))

        # Add priority and insert them to new table.
        for screenshot in screenshots:
            screenshot['priority'] = 0
            api._add_item(context, 'screenshot', screenshot)

        # Set database schema version.
        api.set_version(context, db_version)

    else:
        # Create new tables
        for table in tables:
            for statement in db_connector.to_sql(table):
                cursor.execute(statement)

        # Set database schema version.
        api.set_version(context, db_version)
