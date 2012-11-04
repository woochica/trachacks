import time

from datetime import datetime

from trac.util.datefmt import utc

from announcer.compat import to_utimestamp
 

def do_upgrade(env, ver, cursor):
    """Convert time stamp data and register announcer db schema in
    `system` db table.
    """
    cursor.execute("""
        SELECT id,time,changetime
          FROM subscription
        """)
    result = cursor.fetchall()
    if result:
        cursor.executemany("""
            UPDATE subscription
               SET time=%s,changetime=%s
             WHERE id=%s
            """, [(_iso8601_to_ts(row[1]), _iso8601_to_ts(row[2]), row[0])
                  for row in result])

    cursor.execute("""
        SELECT COUNT(*)
          FROM system
         WHERE name='announcer_version'
    """)
    exists = cursor.fetchone()
    if not exists[0]:
        # Play safe for upgrades from announcer<1.0, that had no version entry.
        cursor.execute("""
            INSERT INTO system
                   (name, value)
            VALUES ('announcer_version', '6')
            """)

def _iso8601_to_ts(s):
    """Parse ISO-8601 string to microsecond POSIX timestamp."""
    try:
        s = str(s)
        if s.isnumeric():
            # Valid type, no conversion required.
            return long(s)
        tm = time.strptime(s, '%Y-%m-%d %H:%M:%S')
        dt = datetime(*(tm[0:6] + (0, utc)))
        return to_utimestamp(dt)
    except (AttributeError, TypeError, ValueError):
        # Create a valid timestamp anyway.
        return to_utimestamp(datetime.now(utc))
