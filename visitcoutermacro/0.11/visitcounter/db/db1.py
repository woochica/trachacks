sql = ['''CREATE TABLE visit (
  id integer PRIMARY KEY,
  page text,
  count integer
);''',
'''INSERT INTO system (name, value) VALUES ('visitcounter_version', 1);''']

def do_upgrade(cursor):
    for statement in sql:
        cursor.execute(statement)
