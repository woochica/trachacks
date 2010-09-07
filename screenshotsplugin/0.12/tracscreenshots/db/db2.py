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
    Column('tags'),
    Column('large_file'),
    Column('medium_file'),
    Column('small_file'),
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

    # Create new tables
    for table in tables:
        for statement in db_connector.to_sql(table):
            cursor.execute(statement)

    if incremental:
        # Get all screenshots from old table.
        columns = ('id', 'name', 'description', 'time', 'author', 'large_file',
          'medium_file', 'small_file', 'component', 'version')
        sql = "SELECT id, name, description, time, author, large_file," \
          " medium_file, small_file, component, version FROM screenshot_old"
        cursor.execute(sql)
        screenshots = []
        for row in cursor:
            row = dict(zip(columns, row))
            screenshots.append(row)

        # Copy them to new tables.
        for screenshot in screenshots:
            sql = "INSERT INTO screenshot (id, name, description, time, " \
              "author, large_file, medium_file, small_file) VALUES (%s, %s, " \
              "%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (screenshot['id'], screenshot['name'],
              screenshot['description'], screenshot['time'],
              screenshot['author'], screenshot['large_file'],
              screenshot['medium_file'], screenshot['small_file']))
            sql = "INSERT INTO screenshot_component (screenshot, component)" \
              " VALUES (%s, %s)"
            cursor.execute(sql, (screenshot['id'], screenshot['component']))
            sql = "INSERT INTO screenshot_version (screenshot, version)" \
              " VALUES (%s, %s)"
            cursor.execute(sql, (screenshot['id'], screenshot['version']))

    # Set database schema version.
    if incremental:
        cursor.execute("UPDATE system SET value = '2' WHERE name = "
          "'screenshots_version'")
    else:
        cursor.execute("INSERT INTO system (name, value) VALUES "
          "('screenshots_version', '2')")
