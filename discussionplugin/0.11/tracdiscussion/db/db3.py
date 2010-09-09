# -*- coding: utf-8 -*-

from trac.db import Table, Column, Index, DatabaseManager

tables = [
  Table('forum', key = 'id')[
    Column('id', type = 'integer', auto_increment = True),
    Column('name'),
    Column('time', type = 'integer'),
    Column('forum_group', type = 'integer'),
    Column('author'),
    Column('moderators'),
    Column('subscribers'),
    Column('subject'),
    Column('description')
  ],
  Table('topic', key = 'id')[
    Column('id', type = 'integer', auto_increment = True),
    Column('forum', type = 'integer'),
    Column('time', type = 'integer'),
    Column('author'),
    Column('subscribers'),
    Column('subject'),
    Column('body')
  ]
]

def do_upgrade(env, cursor):
    db_connector, _ = DatabaseManager(env)._get_connector()

    # Backup old forum table.
    cursor.execute("CREATE TEMPORARY TABLE forum_old AS "
                   "SELECT * "
                   "FROM forum")
    cursor.execute("DROP TABLE forum")

    # Backup old topic table
    cursor.execute("CREATE TEMPORARY TABLE topic_old AS "
                   "SELECT * "
                   "FROM topic")
    cursor.execute("DROP TABLE topic")

    # Create tables.
    for table in tables:
        for statement in db_connector.to_sql(table):
            cursor.execute(statement)

    # Copy old forums.
    cursor.execute("INSERT INTO forum "
                   "(id, name, time, forum_group, author, moderators, subject, "
                     "description) "
                   "SELECT * "
                   "FROM forum_old")
    cursor.execute("UPDATE forum "
                   "SET subscribers = ''")
    cursor.execute("DROP TABLE forum_old")

    # Copy old topics.
    cursor.execute("INSERT INTO topic "
                   "(id, forum, time, author, subject, body) "
                   "SELECT * "
                   "FROM topic_old")
    cursor.execute("UPDATE topic "
                   "SET subscribers = ''")
    cursor.execute("DROP TABLE topic_old")

    # Set database schema version.
    cursor.execute("UPDATE system "
                   "SET value = '3' "
                   "WHERE name = 'discussion_version'")
