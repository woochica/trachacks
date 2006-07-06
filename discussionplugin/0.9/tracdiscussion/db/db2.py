# Common statements
sql = ["""CREATE TABLE forum_group (
  id integer PRIMARY KEY,
  name text,
  description text
);""",
"""ALTER TABLE forum ADD COLUMN forum_group integer;""",
"""ALTER TABLE forum ADD COLUMN author text;""",
"""UPDATE system SET value = 2 WHERE name='discussion_version';"""]

# PostgreSQL statements
postgre_sql = ["""CREATE TABLE forum_group (
  id serial PRIMARY KEY,
  name text,
  description text
);""",
"""ALTER TABLE forum ADD COLUMN forum_group integer;""",
"""ALTER TABLE forum ADD COLUMN author text;""",
"""UPDATE system SET value = 2 WHERE name='discussion_version';"""]

def do_upgrade(env, cursor):
    if env.config.get('trac', 'database').startswith('postgres'):
        for statement in postgre_sql:
            cursor.execute(statement)
    else:
        for statement in sql:
            cursor.execute(statement)
