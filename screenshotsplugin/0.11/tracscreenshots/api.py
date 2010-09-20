# -*- coding: utf-8 -*-

# Standard imports.
import time

# Trac imports.
from trac.core import *
from trac.mimeview import Context
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.util.datefmt import to_datetime, utc, pretty_timedelta
from trac.util.text import to_unicode


class IScreenshotChangeListener(Interface):
    """Extension point interface for components that require notification
    when screenshots are created, modified, or deleted."""

    def screenshot_created(req, screenshot):
        """Called when a screenshot is created. Only argument `screenshot` is
        a dictionary with screenshot field values."""

    def screenshot_changed(req, screenshot, old_screenshot):
        """Called when a screenshot is modified.
        `old_screenshot` is a dictionary containing the previous values of the
        fields and `screenshot` is a dictionary with new values. """

    def screenshot_deleted(req, screenshot):
        """Called when a screenshot is deleted. `screenshot` argument is
        a dictionary with values of fields of just deleted screenshot."""

class IScreenshotsRenderer(Interface):
    """Extension point interface for components providing view on
       screenshots."""

    def render_screenshots(req, name):
        """Provides template and data for screenshots view. Inputs request
           object and dictionary with screenshots data and should return tuple
           with template name and content type."""

    def get_screenshots_view(req):
        """Returns tuple with name and title of implemented screenshots
           view."""

class ScreenshotsApi(Component):

    default_priority = 0

    # Get list functions

    def _get_items(self, context, table, columns, where = '', values = ()):
        sql_values =  {'columns' : ', '.join(columns),
          'table' : table,
          'where' : (' WHERE ' + where) if where else ''}
        sql = ("""SELECT %(columns)s
                  FROM %(table)s
                  %(where)s""" % (sql_values))
        self.log.debug(sql % values)
        context.cursor.execute(sql, values)
        items = []
        for row in context.cursor:
            row = dict(zip(columns, row))
            items.append(row)
        return items

    def get_versions(self, context):
        # Get versions from database.
        return self._get_items(context, 'version', ('name',
          'description'))

    def get_components(self, context):
        # Get components from database.
        return self._get_items(context, 'component',
          ('name', 'description'))

    def get_screenshots(self, context):
        # Get screenshots from database.
        return self._get_items(context, 'screenshot', ('id', 'name',
          'description', 'time', 'author', 'tags', 'file', 'width', 'height',
          'priority'))

    def get_screenshots_complete(self, context):
        screenshots = self.get_screenshots(context)
        for screenshot in screenshots:
            screenshot['components'] = self.get_screenshot_components(context,
              screenshot['id'])
            screenshot['versions'] = self.get_screenshot_versions(context,
              screenshot['id'])
        return screenshots

    def get_filtered_screenshots(self, context, components, versions, relation
      = 'or', orders = ('id', 'name', 'time')):
        has_none_version = True
        has_none_component = True
        columns = ('id', 'name', 'description', 'time', 'author', 'tags',
          'file', 'width', 'height', 'priority')

        # Prepare SQL statement substrings.
        versions_str = (', '.join(['%s'] * len(versions))) or 'NULL'
        components_str = (', '.join(['%s'] * len(components))) or 'NULL'
        orders_str = ', '.join(['%s %s' % (field, direction.upper()) for \
          field, direction in orders])

        # Join them.
        sql_values = {'columns' : ', '.join(columns),
          'versions_str' : versions_str,
          'none_version_exp' : ' OR v.version IS NULL ' if 'none' in versions
            else '',
          'relation' : 'AND' if (relation == 'and') else 'OR',
          'components_str' : components_str,
          'none_components_exp' : ' OR c.component IS NULL ' if 'none' in
            components else '',
          'orders_str' : orders_str}
        sql = ("""SELECT DISTINCT %(columns)s
                  FROM screenshot s
                  LEFT JOIN
                    (SELECT screenshot, version
                    FROM screenshot_version) v
                  ON s.id = v.screenshot
                  LEFT JOIN
                    (SELECT screenshot, component
                    FROM screenshot_component) c
                  ON s.id = c.screenshot
                  WHERE (v.version IN (%(versions_str)s) %(none_version_exp)s)
                    %(relation)s (c.component IN (%(components_str)s)
                      %(none_components_exp)s)
                  ORDER BY %(orders_str)s""" % (sql_values))
        self.log.debug(sql % tuple(versions + components))
        context.cursor.execute(sql, versions + components)
        screenshots = []
        for row in context.cursor:
            row = dict(zip(columns, row))
            screenshots.append(row)
        return screenshots

    def get_new_screenshots(self, context, start, stop):
        columns = ('id', 'name', 'description', 'time', 'author', 'tags',
          'file', 'width', 'height')
        sql_values = {'columns' : ', '.join(columns),
          'start' : start,
          'stop' : stop}
        sql = ("""SELECT %(columns)s
                  FROM screenshot
                  WHERE time
                  BETWEEN %(start)s AND %(stop)s""" % (sql_values))
        self.log.debug(sql)
        context.cursor.execute(sql)
        screenshots = []
        for row in context.cursor:
            row = dict(zip(columns, row))
            screenshots.append(row)
        return screenshots

    # Get one item functions

    def _get_item(self, context, table, columns, where = '', values = ()):
        sql_values = {'columns' : ', '.join(columns),
          'table' : table,
          'where' : (' WHERE ' + where) if where else ''}
        sql = ("""SELECT %(columns)s
                  FROM %(table)s
                  %(where)s""" % (sql_values))
        self.log.debug(sql, values)
        context.cursor.execute(sql, values)
        for row in context.cursor:
            row = dict(zip(columns, row))
            return row

    def _format_screenshot(self, context, screenshot):
        screenshot['author'] = format_to_oneliner(self.env, context,
          screenshot['author'])
        screenshot['name'] = format_to_oneliner(self.env, context,
          screenshot['name'])
        screenshot['description'] = format_to_oneliner(self.env, context,
          screenshot['description'])
        screenshot['width'] = int(screenshot['width'])
        screenshot['height'] = int(screenshot['height'])
        screenshot['time'] = pretty_timedelta(to_datetime(screenshot['time'],
          utc))
        return screenshot

    def get_screenshot(self, context, id):
        # Get screenshot from database.
        screenshot = self._get_item(context, 'screenshot', ('id', 'name',
          'description', 'time', 'author', 'tags', 'file', 'width', 'height',
          'priority'), 'id = %s', (id,))

        if screenshot:
            # Append components and versions.
            screenshot['components'] = self.get_screenshot_components(context,
              screenshot['id'])
            screenshot['versions'] = self.get_screenshot_versions(context,
              screenshot['id'])
            screenshot['width'] = int(screenshot['width'])
            screenshot['height'] = int(screenshot['height'])
            return screenshot
        else:
            return None

    def get_screenshot_by_time(self, context, time):
        # Get screenshot from database.
        screenshot = self._get_item(context, 'screenshot', ('id', 'name',
          'description', 'time', 'author', 'tags', 'file', 'width', 'height',
          'priority'), 'time = %s', (time,))

        if screenshot:
            # Append components and versions.
            screenshot['components'] = self.get_screenshot_components(context,
              screenshot['id'])
            screenshot['versions'] = self.get_screenshot_versions(context,
              screenshot['id'])
            screenshot['width'] = int(screenshot['width'])
            screenshot['height'] = int(screenshot['height'])
            return screenshot
        else:
            return None

    def get_screenshot_components(self, context, id):
        sql_values = {'id' : id}
        sql = ("""SELECT component
                  FROM screenshot_component
                  WHERE screenshot = %(id)s""" % (sql_values))
        self.log.debug(sql)
        context.cursor.execute(sql)
        components = []
        for row in context.cursor:
            components.append(row[0])
        return components

    def get_screenshot_versions(self, context, id):
        sql_values = {'id' : id}
        sql = ("""SELECT version
                  FROM screenshot_version
                  WHERE screenshot = %(id)s""" % (sql_values))
        self.log.debug(sql)
        context.cursor.execute(sql)
        versions = []
        for row in context.cursor:
            versions.append(row[0])
        return versions

    # Add item functions

    def _add_item(self, context, table, item):
        fields = item.keys()
        values = item.values()
        sql_values = {'table' : table,
          'fields' : ', '.join(fields),
          'values' : ', '.join(["%s" for I in range(len(fields))])}
        sql = ("""INSERT INTO %(table)s
                  (%(fields)s)
                  VALUES (%(values)s)""" % (sql_values))
        self.log.debug(sql % tuple(values))
        context.cursor.execute(sql, tuple(values))

    def add_screenshot(self, context, screenshot):
        self._add_item(context, 'screenshot', screenshot)

    def add_component(self, context, component):
        self._add_item(context, 'screenshot_component', component)

    def add_version(self, context, version):
        self._add_item(context, 'screenshot_version', version)

    # Edit item functions

    def _edit_item(self, context, table, id, item):
        fields = item.keys()
        values = item.values()
        sql_values = {'table' : table,
           'fields' : ', '.join([("%s = %%s" % field) for field in fields]),
           'id' : id}
        sql = ("""UPDATE %(table)s
                  SET %(fields)s
                  WHERE id = %(id)s""" % (sql_values))
        self.log.debug(sql % tuple(values))
        context.cursor.execute(sql, tuple(values))

    def edit_screenshot(self, context, id, screenshot):
        # Replace components.
        self.delete_components(context, id)
        for component in screenshot['components']:
            component = {'screenshot' : id,
                         'component' : component}
            self.add_component(context, component)

        # Replace versions.
        self.delete_versions(context, id)
        for version in screenshot['versions']:
            version = {'screenshot' : id,
                       'version' : version}
            self.add_version(context, version)

        # Update screenshot values.
        tmp_screenshot = screenshot.copy()
        del tmp_screenshot['components']
        del tmp_screenshot['versions']
        self._edit_item(context, 'screenshot', id, tmp_screenshot)

    # Delete item functions

    def delete_screenshot(self, context, id):
        # Delete screenshot.
        sql_values = {'id' : id}
        sql = ("""DELETE FROM screenshot
                  WHERE id = %(id)s""" % (sql_values))
        self.log.debug(sql)
        context.cursor.execute(sql)

        # Delete versions and components.
        self.delete_versions(context, id)
        self.delete_components(context, id)

    def delete_versions(self, context, id):
        sql_values = {'id' : id}
        sql = ("""DELETE FROM screenshot_version
                  WHERE screenshot = %(id)s""" % (sql_values))
        self.log.debug(sql)
        context.cursor.execute(sql)

    def delete_components(self, context, id):
        sql_values = {'id' : id}
        sql = ("""DELETE FROM screenshot_component
                  WHERE screenshot = %(id)s""" % (sql_values))
        self.log.debug(sql)
        context.cursor.execute(sql)

    # Other methods.

    def set_version(self, context, version):
        # Check if version item exists.
        sql = ("""SELECT value
                  FROM system
                  WHERE name = 'screenshots_version'""")
        self.log.debug(sql)
        context.cursor.execute(sql)
        in_db = False
        for row in context.cursor:
            in_db = True
            break

        # Insert of update version.
        if in_db:
            sql_values = {'version' : version}
            sql = ("""UPDATE system
                      SET value = %(version)s
                      WHERE name = 'screenshots_version'""" % (sql_values))
        else:
            sql_values = {'version' : version}
            sql = ("""INSERT INTO system (name, value)
                      VALUES ('screenshots_version', %(version)s)""" % (
                     sql_values))
        self.log.debug(sql)
        context.cursor.execute(sql)
