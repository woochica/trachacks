# -*- coding: utf-8 -*-

import os, Image

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
        # Backup old screenshot table.
        cursor.execute("CREATE TEMPORARY TABLE screenshot_old AS SELECT * "
          "FROM screenshot")
        cursor.execute("DROP TABLE screenshot")

        # Create new screenshot table.
        for statement in db_connector.to_sql(tables[0]):
            cursor.execute(statement)

        # Get all screenshots from old table.
        columns = ('id', 'name', 'description', 'time', 'author', 'tags',
          'large_file', 'medium_file', 'small_file')
        sql = 'SELECT ' + ', '.join(columns) + ' FROM screenshot_old'
        cursor.execute(sql)
        screenshots = []
        for row in cursor:
            row = dict(zip(columns, row))
            screenshots.append(row)

        # Rename images and get its dimensions.
        for screenshot in screenshots:
            # Prepare filename of screenshot image.
            path = os.path.join(env.config.get('screenshots', 'path'),
              unicode(screenshot['id']))
            old_filename = screenshot['large_file']

            # Open image to get its dimensions.
            image = Image.open(os.path.join(path, old_filename))
            width = image.size[0]
            height = image.size[1]

            # Prepare new filename.
            name, ext = os.path.splitext(old_filename)
            name = name[:-6]
            ext = ext.lower()
            new_filename = '%s-%sx%s%s' % (name, width, height, ext)

            # Save image under different name.
            image.save(os.path.join(path, new_filename))

            # Remove old image files.
            os.remove(os.path.join(path, screenshot['large_file']))
            os.remove(os.path.join(path, screenshot['medium_file']))
            os.remove(os.path.join(path, screenshot['small_file']))

            # Append new and remove old screenshot attributes.
            screenshot['width'] = width
            screenshot['height'] = height
            screenshot['file'] = name + ext
            del screenshot['large_file']
            del screenshot['medium_file']
            del screenshot['small_file']

        # Copy them to new tables.
        for screenshot in screenshots:
            fields = screenshot.keys()
            values = screenshot.values()
            sql = "INSERT INTO screenshot (" + ", ".join(fields) + \
              ") VALUES (" + ", ".join(["%s" for I in xrange(len(fields))]) \
              + ")"
            cursor.execute(sql, tuple(values))

        # Set database schema version.
        cursor.execute("UPDATE system SET value = '3' WHERE name = "
          "'screenshots_version'")

    else:
        # Create new tables
        for table in tables:
            for statement in db_connector.to_sql(table):
                cursor.execute(statement)

        # Set database schema version.
        cursor.execute("INSERT INTO system (name, value) VALUES "
          "('screenshots_version', '3')")
