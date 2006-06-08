sql = ['''CREATE TABLE forum_group (
  id integer PRIMARY KEY,
  name text,
  description text
);''',
'''ALTER TABLE forum ADD COLUMN forum_group integer;''',
'''ALTER TABLE forum ADD COLUMN author text;''',
'''UPDATE system SET value = "2" WHERE name="discussion_version";''']

def do_upgrade(cursor):
    for statement in sql:
        self.log.debug(statement)
        cursor.execute(statement)
