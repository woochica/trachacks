# Common statements
pre_sql = ["""ALTER TABLE forum RENAME TO tmp_forum""",
"""CREATE TABLE forum (
  id integer PRIMARY KEY,
  name text,
  time integer,
  author text,
  moderators text,
  subject text,
  description text,
  forum_group integer
)""",
"""CREATE TABLE forum_group (
  id integer PRIMARY KEY,
  name text,
  description text
)"""]

post_sql = ["""DROP TABLE tmp_forum""",
"""UPDATE system SET value = '2' WHERE name='discussion_version'"""]

# PostgreSQL statements
pre_postgre_sql = ["""ALTER TABLE forum RENAME TO tmp_forum""",
"""CREATE TABLE forum (
  id serial PRIMARY KEY,
  name text,
  time integer,
  author text,
  moderators text,
  subject text,
  description text,
  forum_group integer
)""",
"""CREATE TABLE forum_group (
  id serial PRIMARY KEY,
  name text,
  description text
)"""]

def do_upgrade(env, cursor):
    if env.config.get('trac', 'database').startswith('postgres'):
        for statement in pre_postgre_sql:
            cursor.execute(statement)
    else:
        for statement in pre_sql:
            cursor.execute(statement)

    columns = ('id', 'name', 'time', 'moderators', 'subject', 'description')
    sql = "SELECT id, name, time, moderators, subject, description FROM" \
      " tmp_forum"
    cursor.execute(sql)
    forums = []
    for row in cursor:
        row = dict(zip(columns, row))
        forums.append(row)

    for forum in forums:
        sql = "INSERT INTO forum (id, name, time, moderators, subject," \
          " description) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (forum['id'], forum['name'], forum['time'],
          forum['moderators'], forum['subject'], forum['description']))

    for statement in post_sql:
        cursor.execute(statement)