sql = ['''CREATE TABLE forum (
  id integer PRIMARY KEY,
  name text,
  time integer,
  moderators text,
  subject text,
  description text
);''',
'''CREATE TABLE topic (
  id integer PRIMARY KEY,
  forum integer,
  time integer,
  author text,
  subject text,
  body text
);''',
'''CREATE TABLE message (
  id integer PRIMARY KEY,
  forum integer,
  topic integer,
  replyto integer,
  time integer,
  author text,
  body text
);''',
'''INSERT INTO system (name, value) VALUES ("discussion_version", 1);''']

def do_upgrade(cursor):
    for statement in sql:
        cursor.execute(statement)
