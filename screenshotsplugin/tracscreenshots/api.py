from trac.core import *
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.util import format_datetime, escape
import time

class ScreenshotsApi(object):

    def __init__(self, component, req):
        self.env = component.env
        self.log = component.log
        self.req = req
        self.db = self.env.get_db_cnx()
        self.cursor = self.db.cursor()

    def __del__(self):
        self.db.commit()

    # Get list functions

    def get_versions(self):
        columns = ('name', 'description')
        sql = "SELECT name, description FROM version"
        self.log.debug(sql)
        self.cursor.execute(sql)
        versions = []
        id = 0
        for row in self.cursor:
            row = dict(zip(columns, row))
            row['description'] = wiki_to_oneliner(row['description'],
              self.env, self.req)
            id = id + 1
            row['id'] = id
            versions.append(row)
        return versions

    def get_components(self):
        columns = ('name', 'description')
        sql = "SELECT name, description FROM component"
        self.log.debug(sql)
        self.cursor.execute(sql)
        components = []
        id = 0
        for row in self.cursor:
            row = dict(zip(columns, row))
            row['description'] = wiki_to_oneliner(row['description'],
              self.env, self.req)
            id = id + 1
            row['id'] = id
            components.append(row)
        return components

    def get_screenshots(self, component, version):
        columns = ('id', 'name', 'description', 'time', 'author', 'large_file',
          'medium_file', 'small_file')
        sql = "SELECT id, name, description, time, author, large_file," \
          " medium_file, small_file FROM screenshot WHERE component = %s AND" \
          " version = %s"
        self.log.debug(sql % (component, version))
        self.cursor.execute(sql, (component, version))
        screenshots = []
        for row in self.cursor:
            row = dict(zip(columns, row))
            row['description'] = wiki_to_oneliner(row['description'], self.env,
              self.req)
            row['author'] = wiki_to_oneliner(row['author'], self.env)
            screenshots.append(row)
        return screenshots

    # Get one item functions

    def get_screenshot(self, id):
        columns = ('id', 'name', 'description', 'time', 'author', 'large_file',
          'medium_file', 'small_file', 'component', 'version')
        sql = "SELECT id, name, description, time, author, large_file," \
          " medium_file, small_file, component, version FROM screenshot" \
          " WHERE id = %s"
        self.log.debug(sql % (id,))
        self.cursor.execute(sql, (id,))
        for row in self.cursor:
            row = dict(zip(columns, row))
            return row

    def get_screenshot_by_time(self, time):
        columns = ('id', 'name', 'description', 'time', 'author', 'large_file',
          'medium_file', 'small_file', 'component', 'version')
        sql = "SELECT id, name, description, time, author, large_file," \
          " medium_file, small_file, component, version FROM screenshot" \
          " WHERE time = %s"
        self.log.debug(sql % (time,))
        self.cursor.execute(sql, (time,))
        for row in self.cursor:
            row = dict(zip(columns, row))
            return row

    # Add item functions

    def add_screenshot(self, name, description, time, author, large_file,
      medium_file, small_file, component, version):
        sql = "INSERT INTO screenshot (name, description, time, author," \
          " large_file, medium_file, small_file, component, version)" \
          " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        self.log.debug(sql % (name, description, time, author, large_file,
          medium_file, small_file, component, version))
        self.cursor.execute(sql, (escape(name), escape(description), time,
          escape(author), large_file, medium_file, small_file, component,
          version))

    # Edit item functions

    def edit_screenshot(self, screenshot, name, description, component,
      version):
        sql = "UPDATE screenshot SET name = %s, description = %s, component" \
          " = %s, version = %s WHERE id = %s"
        self.log.debug(sql % (name, description, component, version, screenshot))
        self.cursor.execute(sql, (escape(name), escape(description), component,
          version, screenshot))

    # Delete item functions

    def delete_screenshot(self, id):
        sql = "DELETE FROM screenshot WHERE id = %s"
        self.log.debug(sql % (id,))
        self.cursor.execute(sql, (id,))
