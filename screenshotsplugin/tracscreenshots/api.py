from trac.core import *
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.util import format_datetime, escape
import time

# Get list functions

def get_versions(cursor, env, req, log):
    columns = ('name', 'description')
    sql = "SELECT name, description FROM version"
    log.debug(sql)
    cursor.execute(sql)
    versions = []
    id = 0
    for row in cursor:
        row = dict(zip(columns, row))
        row['description'] = wiki_to_oneliner(row['description'], env, req)
        id = id + 1
        row['id'] = id
        versions.append(row)
    return versions

def get_components(cursor, env, req, log):
    columns = ('name', 'description')
    sql = "SELECT name, description FROM component"
    log.debug(sql)
    cursor.execute(sql)
    components = []
    id = 0
    for row in cursor:
        row = dict(zip(columns, row))
        row['description'] = wiki_to_oneliner(row['description'], env, req)
        id = id + 1
        row['id'] = id
        components.append(row)
    return components

def get_screenshots(cursor, env, req, log, component, version):
    columns = ('id', 'name', 'description', 'time', 'author', 'large_file',
      'medium_file', 'small_file')
    sql = "SELECT id, name, description, time, author, large_file," \
      " medium_file, small_file FROM screenshot WHERE component = %s AND" \
      " version = %s"
    log.debug(sql)
    cursor.execute(sql, (component, version))
    screenshots = []
    for row in cursor:
        row = dict(zip(columns, row))
        row['description'] = wiki_to_oneliner(row['description'], env, req)
        row['author'] = wiki_to_oneliner(row['author'], env)
        screenshots.append(row)
    return screenshots

# Get one item functions

def get_screenshot(cursor, env, req, log, id):
    columns = ('id', 'name', 'description', 'time', 'author', 'large_file',
      'medium_file', 'small_file', 'component', 'version')
    sql = "SELECT id, name, description, time, author, large_file," \
      " medium_file, small_file, component, version FROM screenshot WHERE" \
      " id = %s"
    log.debug(sql)
    cursor.execute(sql, (id,))
    for row in cursor:
        row = dict(zip(columns, row))
        row['description'] = wiki_to_oneliner(row['description'], env, req)
        row['author'] = wiki_to_oneliner(row['author'], env)
        return row

# Add item functions

def add_screenshot(cursor, log, name, description, author, large_file,
  medium_file, small_file, component, version):
  sql = "INSERT INTO screenshot (name, description, time, author, large_file," \
    " medium_file, small_file, component, version) VALUES (%s, %s, %s, %s, %s," \
    " %s, %s, %s, %s)"
  log.debug(sql)
  cursor.execute(sql, (escape(name), escape(description), int(time.time()),
    escape(author), large_file, medium_file, small_file, component, version))

# Delete item functions

def delete_screenshot(cursor, log, id):
    sql = "DELETE FROM screenshot WHERE id = %s"
    log.debug(sql)
    cursor.execute(sql, (id,))
