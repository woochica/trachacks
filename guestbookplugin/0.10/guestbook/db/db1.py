from trac.db import Table, Column, Index, DatabaseManager

tables = [
  Table('guestbook', key='id')[
    Column('id', type='int', auto_increment = True),
    Column('author'),
    Column('time', type='int'),
    Column('title'),
    Column('body')
  ]
]

def do_upgrade(env, cursor):
    db_connector, _ = DatabaseManager(env)._get_connector()

    # Create tables
    for table in tables:
        for statement in db_connector.to_sql(table):
            cursor.execute(statement)

    # Set database schema version.
    cursor.execute("INSERT INTO system (name, value) VALUES"
      " ('guestbook_version', '1')")
