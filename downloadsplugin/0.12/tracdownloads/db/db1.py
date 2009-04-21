from trac.db import Table, Column, Index, DatabaseManager

# Commont SQL statements

tables = [
  Table('download', key = 'id')[
    Column('id', type = 'integer', auto_increment = True),
    Column('file'),
    Column('description'),
    Column('size', type = 'integer'),
    Column('time', type = 'integer'),
    Column('count', type = 'integer'),
    Column('author'),
    Column('tags'),
    Column('component'),
    Column('version'),
    Column('architecture', type = 'integer'),
    Column('platform', type = 'integer'),
    Column('type', type = 'integer')
  ],
  Table('architecture', key = 'id')[
    Column('id', type = 'integer', auto_increment = True),
    Column('name'),
    Column('description')
  ],
  Table('platform', key = 'id')[
    Column('id', type = 'integer', auto_increment = True),
    Column('name'),
    Column('description')
  ],
  Table('download_type', key = 'id')[
    Column('id', type = 'integer', auto_increment = True),
    Column('name'),
    Column('description')
  ]
]

values = ["INSERT INTO architecture (name) VALUES ('alpha')",
  "INSERT INTO architecture (name) VALUES ('arm')",
  "INSERT INTO architecture (name) VALUES ('i386')",
  "INSERT INTO architecture (name) VALUES ('ia64')",
  "INSERT INTO architecture (name) VALUES ('powerpc')",
  "INSERT INTO architecture (name) VALUES ('sparc')",
  "INSERT INTO architecture (name) VALUES ('other')",
  "INSERT INTO platform (name) VALUES ('Windows')",
  "INSERT INTO platform (name) VALUES ('Linux')",
  "INSERT INTO platform (name) VALUES ('MacOS')",
  "INSERT INTO platform (name) VALUES ('other')",
  "INSERT INTO download_type (name) VALUES ('binary')",
  "INSERT INTO download_type (name) VALUES ('source')",
  "INSERT INTO download_type (name) VALUES ('data')",
  "INSERT INTO download_type (name) VALUES ('other')",
  "INSERT INTO system (name, value) VALUES ('downloads_description', 'Here is a list of available downloads:')"
]

def do_upgrade(env, cursor):
    db_connector, _ = DatabaseManager(env)._get_connector()

    # Create tables
    for table in tables:
        for statement in db_connector.to_sql(table):
            cursor.execute(statement)

    # Insert default values
    for statement in values:
        cursor.execute(statement)

    # Set database schema version.
    cursor.execute("INSERT INTO system (name, value) VALUES"
      " ('downloads_version', '1')")
