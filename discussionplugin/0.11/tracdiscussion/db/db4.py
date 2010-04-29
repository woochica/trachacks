# -*- coding: utf-8 -*-

from trac.db import DatabaseManager

def do_upgrade(env, cursor):
    db_connector, _ = DatabaseManager(env)._get_connector()

    # Create indices for forum, topic and message times.
    cursor.execute("CREATE INDEX forum_time_idx ON forum (time)")
    cursor.execute("CREATE INDEX topic_time_idx ON topic (time)")
    cursor.execute("CREATE INDEX message_time_idx ON message (time)")

    # Set database schema version.
    cursor.execute("UPDATE system SET value = '4' WHERE" \
      " name = 'discussion_version'")
