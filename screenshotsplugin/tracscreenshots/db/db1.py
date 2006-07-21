# Commont SQL statements
sql = ["""CREATE TABLE screenshot (
  id integer PRIMARY KEY,
  name text,
  description text,
  time integer,
  author text,
  large_file text,
  medium_file text,
  small_file text,
  component text,
  version text
);""",
"""INSERT INTO system (name, value) VALUES ('screenshots_version', '1')"""]

# PostgreSQL statements
postgre_sql = ["""CREATE TABLE screenshot (
  id serial PRIMARY KEY,
  name text,
  description text,
  time integer,
  author text,
  large_file text,
  medium_file text,
  small_file text,
  component text,
  version text
);""",
"""INSERT INTO system (name, value) VALUES ('screenshots_version', '1')"""]

def do_upgrade(env, cursor):
    if env.config.get('trac', 'database').startswith('postgres'):
        for statement in postgre_sql:
            cursor.execute(statement)
    else:
        for statement in sql:
            cursor.execute(statement)
