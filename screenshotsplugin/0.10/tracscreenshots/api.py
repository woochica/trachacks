# -*- coding: utf8 -*-

import time

from trac.core import *
from trac.config import Option
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.util import format_datetime, pretty_timedelta

class IScreenshotChangeListener(Interface):
    """Extension point interface for components that require notification
    when screenshots are created, modified, or deleted."""

    def screenshot_created(screenshot):
        """Called when a screenshot is created. Only argument `screenshot` is
        a dictionary with screenshot field values."""

    def screenshot_changed(screenshot, old_screenshot):
        """Called when a screenshot is modified.
        `old_screenshot` is a dictionary containing the previous values of the
        fields and `screenshot` is a dictionary with new values. """

    def screenshot_deleted(screenshot):
        """Called when a screenshot is deleted. `screenshot` argument is
        a dictionary with values of fields of just deleted screenshot."""

class IScreenshotsRenderer(Interface):
    """Extension point interface for components providing view on
       screenshots."""

    def render_screenshots(req, name, data):
        """Provides template and data for screenshots view. Inputs request
           object and dictionary with screenshots data and should return tuple
           with template name modified or unchanged data and content type."""

    def get_screenshots_view(req):
        """Returns tuple with name and title of implemented screenshots
           view."""

class ScreenshotsApi(Component):

    # Get list functions

    def _get_items(self, cursor, table, columns, where = '', value = None):
        sql = 'SELECT ' + ', '.join(columns) + ' FROM ' + table + ' ' + where
        if where:
            self.log.debug(sql % (value,))
            cursor.execute(sql, (value,))
        else:
            self.log.debug(sql)
            cursor.execute(sql)
        items = []
        for row in cursor:
            row = dict(zip(columns, row))
            items.append(row)
        return items

    def get_versions(self, cursor):
        # Get versions from database.
        versions = self._get_items(cursor, 'version', ('name', 'description'))

        # Prepare them for display.
        for version in versions:
            version['description'] = wiki_to_oneliner(version['description'],
              self.env)
        return versions

    def get_components(self, cursor):
        # Get components from database.
        components = self._get_items(cursor, 'component', ('name',
          'description'))

        # Prepare them for display.
        for component in components:
            component['description'] = wiki_to_oneliner(
              component['description'], self.env)
        return components

    def get_screenshots(self, cursor):
        # Get screenshots from database.
        screenshots = self._get_items(cursor, 'screenshot', ('id', 'name',
          'description', 'time', 'author', 'tags', 'file', 'width', 'height'))

        # Prepare them for display.
        for screenshot in screenshots:
            screenshot['name'] = wiki_to_oneliner(screenshot['name'], self.env)
            screenshot['description'] = wiki_to_oneliner(
              screenshot['description'], self.env)
            screenshot['author'] = wiki_to_oneliner(screenshot['author'],
              self.env)
        return screenshots

    # Get one item functions

    def _get_item(self, cursor, table, columns, where = '', value = None):
        sql = 'SELECT ' + ', '.join(columns) + ' FROM ' + table + ' ' + where
        if where:
            self.log.debug(sql % (value,))
            cursor.execute(sql, (value,))
        else:
            self.log.debug(sql)
            cursor.execute(sql)
        items = []
        for row in cursor:
            row = dict(zip(columns, row))
            return row

    def get_screenshot(self, cursor, id):
        # Get screenshot from database.
        screenshot = self._get_item(cursor, 'screenshot', ('id', 'name',
          'description', 'time', 'author', 'tags', 'file', 'width', 'height'),
          'WHERE id = %s', id)

        # Prepare it for display.
        if screenshot:
            screenshot['components'] = self.get_screenshot_components(cursor,
              screenshot['id'])
            screenshot['versions'] = self.get_screenshot_versions(cursor,
              screenshot['id'])
            screenshot['width'] = int(screenshot['width'])
            screenshot['height'] = int(screenshot['height'])
            screenshot['time'] = pretty_timedelta(screenshot['time'])
            return screenshot
        else:
            return None

    def get_screenshot_by_time(self, cursor, time):
        # Get screenshot from database.
        screenshot = self._get_item(cursor, 'screenshot', ('id', 'name',
          'description', 'time', 'author', 'tags', 'file', 'width', 'height'),
          'WHERE time = %s', time)

        #Prepare it for display.
        screenshot['components'] = self.get_screenshot_components(cursor,
          screenshot['id'])
        screenshot['versions'] = self.get_screenshot_versions(cursor,
          screenshot['id'])
        screenshot['width'] = int(screenshot['width'])
        screenshot['height'] = int(screenshot['height'])
        screenshot['time'] = pretty_timedelta(screenshot['time'])
        return screenshot

    def get_screenshot_components(self, cursor, id):
        sql = 'SELECT component FROM screenshot_component WHERE screenshot = %s'
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))
        components = []
        for row in cursor:
            components.append(row[0])
        return components

    def get_screenshot_versions(self, cursor, id):
        sql = 'SELECT version FROM screenshot_version WHERE screenshot = %s'
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))
        versions = []
        for row in cursor:
            versions.append(row[0])
        return versions

    # Add item functions

    def _add_item(self, cursor, table, item):
        fields = item.keys()
        values = item.values()
        sql = "INSERT INTO %s (" % (table,) + ", ".join(fields) + ") VALUES (" \
          + ", ".join(["%s" for I in xrange(len(fields))]) + ")"
        self.log.debug(sql % tuple(values))
        cursor.execute(sql, tuple(values))

    def add_screenshot(self, cursor, screenshot):
        self._add_item(cursor, 'screenshot', screenshot)

    def add_component(self, cursor, component):
        self._add_item(cursor, 'screenshot_component', component)

    def add_version(self, cursor, version):
        self._add_item(cursor, 'screenshot_version', version)

    # Edit item functions

    def _edit_item(self, cursor, table, id, item):
        fields = item.keys()
        values = item.values()
        sql = "UPDATE %s SET " % (table,) + ", ".join([("%s = %%s" % (field))
          for field in fields]) + " WHERE id = %s"
        self.log.debug(sql % tuple(values + [id]))
        cursor.execute(sql, tuple(values + [id]))

    def edit_screenshot(self, cursor, id, screenshot):
        # Replace components.
        self.delete_components(cursor, id)
        for component in screenshot['components']:
            component = {'screenshot' : id,
                         'component' : component}
            self.add_component(cursor, component)

        # Replace versions.
        self.delete_versions(cursor, id)
        for version in screenshot['versions']:
            version = {'screenshot' : id,
                       'version' : version}
            self.add_version(cursor, version)

        # Update screenshot values.
        del screenshot['components']
        del screenshot['versions']
        self._edit_item(cursor, 'screenshot', id, screenshot)


    # Delete item functions

    def delete_screenshot(self, cursor, id):
        # Delete screenshot.
        sql = "DELETE FROM screenshot WHERE id = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))

        # Delete versions and components.
        self.delete_versions(cursor, id)
        self.delete_components(cursor, id)

    def delete_versions(self, cursor, id):
        sql = "DELETE FROM screenshot_version WHERE screenshot = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))

    def delete_components(self, cursor, id):
        sql = "DELETE FROM screenshot_component WHERE screenshot = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))
