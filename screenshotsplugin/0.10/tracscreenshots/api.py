# -*- coding: utf-8 -*-

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

    def _get_items(self, cursor, table, columns, where = '', values = ()):
        sql = 'SELECT ' + ', '.join(columns) + ' FROM ' + table + (where
          and (' WHERE ' + where) or '')
        self.log.debug(sql % values)
        cursor.execute(sql, values)
        items = []
        for row in cursor:
            row = dict(zip(columns, row))
            items.append(row)
        return items

    def get_versions(self, cursor):
        # Get versions from database.
        return self._get_items(cursor, 'version', ('name',
          'description'))

    def get_components(self, cursor):
        # Get components from database.
        return self._get_items(cursor, 'component',
          ('name', 'description'))

    def get_screenshots(self, cursor):
        # Get screenshots from database.
        return self._get_items(cursor, 'screenshot', ('id', 'name',
          'description', 'time', 'author', 'tags', 'file', 'width', 'height'))

    def get_screenshots_complete(self, cursor):
        screenshots = self.get_screenshots(cursor)
        for screenshot in screenshots:
            screenshot['components'] = self.get_screenshot_components(cursor,
              screenshot['id'])
            screenshot['versions'] = self.get_screenshot_versions(cursor,
              screenshot['id'])
        return screenshots

    def get_filtered_screenshots(self, cursor, components, versions):
        has_none_version = True
        has_none_component = True
        columns = ('id', 'name', 'description', 'time', 'author', 'tags',
          'file', 'width', 'height')
        versions_str = (', '.join(['%s'] * len(versions))) or 'NULL'
        components_str = (', '.join(['%s'] * len(components))) or 'NULL'
        sql = 'SELECT DISTINCT ' + ', '.join(columns) + ' FROM screenshot s ' \
          'LEFT JOIN (SELECT screenshot, version FROM screenshot_version) v ' \
          'ON s.id = v.screenshot LEFT JOIN (SELECT screenshot, component ' \
          'FROM screenshot_component) c ON s.id = c.screenshot WHERE ' \
          'v.version IN (' + versions_str + ')' + (('none' in versions) and \
          ' OR v.version IS NULL' or '') + ' OR c.component IN (' + \
          components_str + ')' + (('none' in components) and \
          ' OR c.component IS NULL' or '')
        self.log.debug(versions + components)
        self.log.debug(sql % tuple(versions + components))
        cursor.execute(sql, versions + components)
        screenshots = []
        for row in cursor:
            row = dict(zip(columns, row))
            screenshots.append(row)
        return screenshots

    # Get one item functions

    def _get_item(self, cursor, table, columns, where = '', values = ()):
        sql = 'SELECT ' + ', '.join(columns) + ' FROM ' + table + (where
          and (' WHERE ' + where) or '')
        self.log.debug(sql, values)
        cursor.execute(sql, values)
        for row in cursor:
            row = dict(zip(columns, row))
            return row

    def get_screenshot(self, cursor, id):
        # Get screenshot from database.
        screenshot = self._get_item(cursor, 'screenshot', ('id', 'name',
          'description', 'time', 'author', 'tags', 'file', 'width', 'height'),
          'id = %s', (id,))

        if screenshot:
            # Append components and versions.
            screenshot['components'] = self.get_screenshot_components(cursor,
              screenshot['id'])
            screenshot['versions'] = self.get_screenshot_versions(cursor,
              screenshot['id'])
            return screenshot
        else:
            return None

    def get_screenshot_by_time(self, cursor, time):
        # Get screenshot from database.
        screenshot = self._get_item(cursor, 'screenshot', ('id', 'name',
          'description', 'time', 'author', 'tags', 'file', 'width', 'height'),
          'time = %s', (time,))

        # Append components and versions.
        if screenshot:
            screenshot['components'] = self.get_screenshot_components(cursor,
              screenshot['id'])
            screenshot['versions'] = self.get_screenshot_versions(cursor,
              screenshot['id'])
            return screenshot
        else:
            return None

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
