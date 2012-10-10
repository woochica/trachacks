# -*- coding: utf-8 -*-

from trac.core import *
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.util import format_datetime, escape
import time

class ScreenshotsApi(object):

    def __init__(self, component):
        self.env = component.env
        self.log = component.log

    # Get list functions

    def get_versions(self, cursor):
        columns = ('name', 'description')
        sql = "SELECT name, description FROM version"
        self.log.debug(sql)
        cursor.execute(sql)
        versions = []
        id = 0
        for row in cursor:
            row = dict(zip(columns, row))
            row['description'] = wiki_to_oneliner(row['description'],
              self.env)
            id = id + 1
            row['id'] = id
            versions.append(row)
        return versions

    def get_components(self, cursor):
        columns = ('name', 'description')
        sql = "SELECT name, description FROM component"
        self.log.debug(sql)
        cursor.execute(sql)
        components = []
        id = 0
        for row in cursor:
            row = dict(zip(columns, row))
            row['description'] = wiki_to_oneliner(row['description'],
              self.env)
            id = id + 1
            row['id'] = id
            components.append(row)
        return components

    def get_screenshots(self, cursor, component, version):
        columns = ('id', 'name', 'description', 'time', 'author', 'tags',
          'large_file', 'medium_file', 'small_file')
        sql = "SELECT s.id, s.name, s.description, s.time, s.author, s.tags," \
          " s.large_file, s.medium_file, s.small_file FROM screenshot s," \
          " screenshot_component c, screenshot_version v WHERE c.component" \
          " = %s AND v.version = %s AND s.id = c.screenshot AND s.id =" \
          " v.screenshot;"
        self.log.debug(sql % (component, version))
        cursor.execute(sql, (component, version))
        screenshots = []
        for row in cursor:
            row = dict(zip(columns, row))
            row['name'] = wiki_to_oneliner(row['name'], self.env)
            row['description'] = wiki_to_oneliner(row['description'], self.env)
            row['author'] = wiki_to_oneliner(row['author'], self.env)
            screenshots.append(row)
        return screenshots

    # Get one item functions

    def get_screenshot(self, cursor, id):
        columns = ('id', 'name', 'description', 'time', 'author', 'tags',
          'large_file', 'medium_file', 'small_file')
        sql = "SELECT id, name, description, time, author, tags, large_file," \
          " medium_file, small_file FROM screenshot" \
          " WHERE id = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))
        for row in cursor:
            row = dict(zip(columns, row))
            row['components'] = self.get_screenshot_components(cursor,
              row['id'])
            row['versions'] = self.get_screenshot_versions(cursor, row['id'])
            return row

    def get_screenshot_by_time(self, cursor, time):
        columns = ('id', 'name', 'description', 'time', 'author', 'tags',
          'large_file', 'medium_file', 'small_file')
        sql = "SELECT id, name, description, time, author, tags, large_file," \
          " medium_file, small_file FROM screenshot" \
          " WHERE time = %s"
        self.log.debug(sql % (time,))
        cursor.execute(sql, (time,))
        for row in cursor:
            row = dict(zip(columns, row))
            row['components'] = self.get_screenshot_components(cursor,
              row['id'])
            row['versions'] = self.get_screenshot_versions(cursor, row['id'])
            return row

    def get_screenshot_components(self, cursor, screenshot):
        sql = "SELECT component FROM screenshot_component WHERE screenshot =" \
          " %s"
        self.log.debug(sql % (screenshot,))
        cursor.execute(sql, (screenshot,))
        components = []
        for row in cursor:
            components.append(row[0])
        return components

    def get_screenshot_versions(self, cursor, screenshot):
        sql = "SELECT version FROM screenshot_version WHERE screenshot =" \
          " %s"
        self.log.debug(sql % (screenshot,))
        cursor.execute(sql, (screenshot,))
        versions = []
        for row in cursor:
            versions.append(row[0])
        return versions

    # Add item functions

    def add_screenshot(self, cursor, name, description, time, author, tags,
      large_file, medium_file, small_file):
        sql = "INSERT INTO screenshot (name, description, time, author, tags," \
          " large_file, medium_file, small_file) VALUES (%s, %s, %s, %s, %s," \
          " %s, %s, %s)"
        self.log.debug(sql % (name, description, time, author, tags, large_file,
          medium_file, small_file))
        cursor.execute(sql, (escape(name), escape(description), time,
          escape(author), tags, large_file, medium_file, small_file))

    def add_component(self, cursor, screenshot, component):
        sql = "INSERT INTO screenshot_component (screenshot, component)" \
          " VALUES (%s, %s)"
        self.log.debug(sql % (screenshot, component))
        cursor.execute(sql, (screenshot, component))

    def add_version(self, cursor, screenshot, version):
        sql = "INSERT INTO screenshot_version (screenshot, version)" \
          " VALUES (%s, %s)"
        self.log.debug(sql % (screenshot, version))
        cursor.execute(sql, (screenshot, version))

    # Edit item functions

    def edit_screenshot(self, cursor, screenshot, name, description, tags, components,
      versions):
        # Update screenshot values.
        sql = "UPDATE screenshot SET name = %s, description = %s, tags = %s" \
          " WHERE id = %s"
        self.log.debug(sql % (name, description, tags, screenshot))
        cursor.execute(sql, (escape(name), escape(description), tags,
          screenshot))

        # Replace components
        sql = "DELETE FROM screenshot_component WHERE screenshot = %s"
        self.log.debug(sql % (screenshot,))
        cursor.execute(sql, (screenshot,))
        for component in components:
            self.add_component(cursor, screenshot, component)

        # Replace versions
        sql = "DELETE FROM screenshot_version WHERE screenshot = %s"
        self.log.debug(sql % (screenshot,))
        cursor.execute(sql, (screenshot,))
        for version in versions:
            self.add_version(cursor, screenshot, version)

    # Delete item functions

    def delete_screenshot(self, cursor, id):
        sql = "DELETE FROM screenshot WHERE id = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))
        sql = "DELETE FROM screenshot_component WHERE screenshot = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))
        sql = "DELETE FROM screenshot_version WHERE screenshot = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))
