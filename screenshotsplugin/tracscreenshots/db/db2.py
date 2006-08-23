# Commont SQL statements
pre_sql = ["""ALTER TABLE screenshot RENAME TO tmp_screenshot""",
"""CREATE TABLE screenshot (
  id integer PRIMARY KEY,
  name text,
  description text,
  time integer,
  author text,
  tags text,
  large_file text,
  medium_file text,
  small_file text
)""",
"""CREATE TABLE screenshot_component (
  id integer PRIMARY KEY,
  screenshot integer,
  component text
)""",
"""CREATE TABLE screenshot_version (
  id integer PRIMARY KEY,
  screenshot integer,
  version text
)"""]

post_sql = ["""DROP TABLE tmp_screenshot""",
"""UPDATE system SET value = '2' WHERE name = 'screenshots_version'"""]

# PostgreSQL statements
pre_postgre_sql = ["""ALTER TABLE screenshot RENAME TO tmp_screenshot""",
"""CREATE TABLE screenshot (
  id serial PRIMARY KEY,
  name text,
  description text,
  time integer,
  author text,
  tags, text,
  large_file text,
  medium_file text,
  small_file text
)""",
"""CREATE TABLE screenshot_component (
  id serial PRIMARY KEY,
  screenshot integer,
  component text
)""",
"""CREATE TABLE screenshot_version (
  id serial PRIMARY KEY,
  screenshot integer,
  version text
)"""]

def do_upgrade(env, cursor):
    # Prepare old and new tables.
    if env.config.get('trac', 'database').startswith('postgres'):
        for statement in pre_postgre_sql:
            cursor.execute(statement)
    else:
        for statement in pre_sql:
            cursor.execute(statement)

    # Get all screenshots from old table.
    columns = ('id', 'name', 'description', 'time', 'author', 'large_file',
          'medium_file', 'small_file', 'component', 'version')
    sql = "SELECT id, name, description, time, author, large_file," \
          " medium_file, small_file, component, version FROM tmp_screenshot"
    cursor.execute(sql)
    screenshots = []
    for row in cursor:
        row = dict(zip(columns, row))
        screenshots.append(row)

    # Copy them to new tables.
    for screenshot in screenshots:
        sql = "INSERT INTO screenshot (id, name, description, time, author," \
          " large_file, medium_file, small_file) VALUES (%s, %s, %s, %s, %s," \
          " %s, %s, %s)"
        cursor.execute(sql, (screenshot['id'], screenshot['name'],
          screenshot['description'], screenshot['time'], screenshot['author'],
          screenshot['large_file'], screenshot['medium_file'],
          screenshot['small_file']))
        sql = "INSERT INTO screenshot_component (screenshot, component)" \
          " VALUES (%s, %s)"
        cursor.execute(sql, (screenshot['id'], screenshot['component']))
        sql = "INSERT INTO screenshot_version (screenshot, version)" \
          " VALUES (%s, %s)"
        cursor.execute(sql, (screenshot['id'], screenshot['version']))

    # Finish upgrade.
    for statement in post_sql:
        cursor.execute(statement)
