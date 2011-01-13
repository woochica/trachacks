# -*- coding: utf-8 -*-

from trac.db import Table, Column, Index, DatabaseManager

tables = [
  Table('topic', key = 'id')[
    Column('id', type = 'integer', auto_increment = True),
    Column('forum', type = 'integer'),
    Column('time', type = 'integer'),
    Column('author'),
    Column('subscribers'),
    Column('subject'),
    Column('body'),
  ]
]

def do_upgrade(env, cursor):
    db_connector, _ = DatabaseManager(env)._get_connector()

    # Backup old topic table
    cursor.execute("CREATE TEMPORARY TABLE topic_old AS "
                   "SELECT * "
                   "FROM topic")
    cursor.execute("DROP TABLE topic")

    # Create tables.
    for table in tables:
        for statement in db_connector.to_sql(table):
            cursor.execute(statement)

    # Add two columns that uses constraints.
    # TODO: No other way how to do it.
    cursor.execute("ALTER TABLE topic ADD COLUMN status INT DEFAULT 0 NOT NULL")
    cursor.execute("ALTER TABLE topic ADD COLUMN priority INT DEFAULT 0 NOT NULL")

    # Copy old topics.
    cursor.execute("INSERT INTO topic "
                   "(id, forum, time, author, subscribers, subject, body, "
                     "status, priority) "
                   "SELECT id, forum, time, author, subscribers, subject, "
                     "body, 0, 0 "
                   "FROM topic_old")
    cursor.execute("DROP TABLE topic_old")

    # Set database schema version.
    cursor.execute("UPDATE system "
                   "SET value = '5' "
                   "WHERE name = 'discussion_version'")
