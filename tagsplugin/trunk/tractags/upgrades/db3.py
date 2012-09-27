def do_upgrade(env, ver, cursor):
    """Register tractags db schema in `system` db table."""

    cursor.execute("""
        SELECT COUNT(*)
          FROM system
         WHERE name='tags_version'
    """)
    exists = cursor.fetchone()
    if not exists[0]:
        # Play safe for upgrades from tags<0.7, that had no version entry.
        cursor.execute("""
            INSERT INTO system
                   (name, value)
            VALUES ('tags_version', '2')
            """)
