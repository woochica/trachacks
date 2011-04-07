# -*- coding: utf-8 -*-

# Standard imports.
import os, shutil, re, mimetypes, unicodedata
from datetime import *

# Trac imports
from trac.core import *
from trac.config import Option, IntOption, BoolOption, ListOption, PathOption
from trac.resource import Resource
from trac.mimeview import Mimeview, Context
from trac.web.chrome import add_stylesheet, add_script
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.util.datefmt import to_timestamp, to_datetime, utc, \
  format_datetime, pretty_timedelta
from trac.util.text import to_unicode, unicode_unquote, unicode_quote, \
  pretty_size

class IDownloadChangeListener(Interface):
    """Extension point interface for components that require notification
    when downloads are created, modified, or deleted."""

    def download_created(context, download):
        """Called when a download is created. Only argument `download` is
        a dictionary with download field values."""

    def download_changed(context, download, old_download):
        """Called when a download is modified.
        `old_download` is a dictionary containing the previous values of the
        fields and `download` is a dictionary with new values. """

    def download_deleted(context, download):
        """Called when a download is deleted. `download` argument is
        a dictionary with values of fields of just deleted download."""

class DownloadsApi(Component):

    # Download change listeners.
    change_listeners = ExtensionPoint(IDownloadChangeListener)

    # Configuration options.
    title = Option('downloads', 'title', 'Downloads',
      doc = 'Main navigation bar button title.')
    path = PathOption('downloads', 'path', '../downloads',
      doc = 'Path where to store uploaded downloads.')
    ext = ListOption('downloads', 'ext', 'zip,gz,bz2,rar',
      doc = 'List of file extensions allowed to upload.')
    max_size = IntOption('downloads', 'max_size', 268697600,
      'Maximum allowed file size (in bytes) for downloads. Default is 256 MB.')
    visible_fields = ListOption('downloads', 'visible_fields',
      'id,file,description,size,time,count,author,tags,component,version,'
      'architecture,platform,type', doc = 'List of downloads table fields that'
      ' should be visible to users on Downloads section.')
    download_sort = Option('downloads', 'download_sort', 'time', 'Column by'
      ' which downloads list will be sorted. Possible values are: id, file,'
      ' description, size, time, count, author, tags, component, version,'
      ' architecture, platform, type. Default value is: time.')
    download_sort_direction = Option('downloads', 'download_sort_direction',
      'desc', 'Direction of downloads list sorting. Possible values are: asc,'
      ' desc. Default value is: desc.')
    architecture_sort = Option('downloads', 'architecture_sort', 'name',
      'Column by which architectures list will be sorted. Possible values are:'
      ' id, name, description. Default value is: name.')
    architecture_sort_direction = Option('downloads',
      'architecture_sort_direction', 'asc', 'Direction of architectures list'
      ' sorting. Possible values are: asc, desc. Default value is: asc.')
    platform_sort = Option('downloads', 'platform_sort', 'name', 'Column by'
      ' which platforms list will be sorted. Possible values are: id, name,'
      ' description. Default value is: name.')
    platform_sort_direction = Option('downloads', 'platform_sort_direction',
      'asc', 'Direction of platforms list sorting. Possible values are: asc,'
      ' desc. Default value is: asc.')
    type_sort = Option('downloads', 'type_sort', 'name', 'Column by which types'
      ' list will be sorted. Possible values are: id, name, description.'
      ' Default value is: name.')
    type_sort_direction = Option('downloads', 'type_sort_direction', 'asc',
      'Direction of types list sorting. Possible values are: asc, desc. Default'
      ' value is: asc.')
    unique_filename = BoolOption('downloads', 'unique_filename', False,
      doc = 'If enabled checks if uploaded file has unique name.')

    # Get list functions.

    def _get_items(self, context, table, columns, where = '', values = (),
      order_by = '', desc = False):
        sql = 'SELECT ' + ', '.join(columns) + ' FROM ' + table + (where
          and (' WHERE ' + where) or '') + (order_by and (' ORDER BY ' +
          order_by + (' ASC', ' DESC')[bool(desc)]) or '')
        self.log.debug(sql % values)
        context.cursor.execute(sql, values)
        items = []
        for row in context.cursor:
            row = dict(zip(columns, row))
            items.append(row)
        return items

    def get_versions(self, context, order_by = 'name', desc = False):
        # Get versions from table.
        versions = self._get_items(context, 'version', ('name', 'description'),
          order_by = order_by, desc = desc)

        # Add IDs to versions according to selected sorting.
        id = 0
        for version in versions:
            id = id + 1
            version['id'] = id
        return versions

    def get_components(self, context, order_by = '', desc = False):
        # Get components from table.
        components = self._get_items(context, 'component', ('name', 
          'description'), order_by = order_by, desc = desc)

        # Add IDs to versions according to selected sorting.
        id = 0
        for component in components:
            id = id + 1
            component['id'] = id
        return components

    def get_downloads(self, context, order_by = 'id', desc = False):
        # Get downloads from table.
        downloads = self._get_items(context, 'download', ('id', 'file',
          'description', 'size', 'time', 'count', 'author', 'tags', 'component',
          'version', 'architecture', 'platform', 'type'), order_by = order_by,
          desc = desc)

        # Replace field IDs with apropriate objects.
        for download in downloads:
            download['architecture'] = self.get_architecture(context,
              download['architecture'])
            download['platform'] = self.get_platform(context,
              download['platform'])
            download['type'] = self.get_type(context, download['type'])
        return downloads

    def get_new_downloads(self, context, start, stop, order_by = 'time',
        desc = False):
        return self._get_items(context, 'download', ('id', 'file',
          'description', 'size', 'time', 'count', 'author', 'tags', 'component',
          'version', 'architecture', 'platform', 'type'), 'time BETWEEN %s AND'
          ' %s', (start, stop), order_by = order_by, desc = desc)

    def get_architectures(self, context, order_by = 'id', desc = False):
        return self._get_items(context, 'architecture', ('id', 'name',
           'description'), order_by = order_by, desc = desc)

    def get_platforms(self, context, order_by = 'id', desc = False):
        return self._get_items(context, 'platform', ('id', 'name',
          'description'), order_by = order_by, desc = desc)

    def get_types(self, context, order_by = 'id', desc = False):
        return self._get_items(context, 'download_type', ('id', 'name',
          'description'), order_by = order_by, desc = desc)

    # Get one item functions.

    def _get_item(self, context, table, columns, where = '', values = ()):
        sql = 'SELECT ' + ', '.join(columns) + ' FROM ' + table + (where
          and (' WHERE ' + where) or '')
        self.log.debug(sql % values)
        context.cursor.execute(sql, values)
        for row in context.cursor:
            row = dict(zip(columns, row))
            return row
        return None

    def get_download(self, context, id):
        return self._get_item(context, 'download', ('id', 'file', 'description',
          'size', 'time', 'count', 'author', 'tags', 'component', 'version',
          'architecture', 'platform', 'type'), 'id = %s', (id,))

    def get_download_by_time(self, context, time):
        return self._get_item(context, 'download', ('id', 'file', 'description',
          'size', 'time', 'count', 'author', 'tags', 'component', 'version',
          'architecture', 'platform', 'type'), 'time = %s', (time,))

    def get_download_by_file(self, context, file):
        return self._get_item(context, 'download', ('id', 'file', 'description',
          'size', 'time', 'count', 'author', 'tags', 'component',  'version',
          'architecture', 'platform', 'type'), 'file = %s', (file,))

    def get_architecture(self, context, id):
        architecture = self._get_item(context, 'architecture', ('id', 'name',
          'description'), 'id = %s', (id,))
        if not architecture:
            architecture = {'id' : 0, 'name' : '', 'description' : ''}
        return architecture

    def get_architecture_by_name(self, context, name):
        architecture = self._get_item(context, 'architecture', ('id', 'name',
          'description'), 'name = %s', (name,))
        if not architecture:
            architecture = {'id' : 0, 'name' : '', 'description' : ''}
        return architecture

    def get_platform(self, context, id):
        platform = self._get_item(context, 'platform', ('id', 'name',
          'description'), 'id = %s', (id,))
        if not platform:
            platform = {'id' : 0, 'name' : '', 'description' : ''}
        return platform

    def get_platform_by_name(self, context, name):
        platform = self._get_item(context, 'platform', ('id', 'name',
          'description'), 'name = %s', (name,))
        if not platform:
            platform = {'id' : 0, 'name' : '', 'description' : ''}
        return platform

    def get_type(self, context, id):
        type = self._get_item(context, 'download_type', ('id', 'name',
          'description'), 'id = %s', (id,))
        if not type:
            type = {'id' : 0, 'name' : '', 'description' : ''}
        return type

    def get_type_by_name(self, context, name):
        type = self._get_item(context, 'download_type', ('id', 'name',
          'description'), 'name = %s', (name,))
        if not type:
            type = {'id' : 0, 'name' : '', 'description' : ''}
        return type

    def get_description(self, context):
        sql = "SELECT value FROM system WHERE name = 'downloads_description'"
        self.log.debug(sql)
        context.cursor.execute(sql)
        for row in context.cursor:
            return row[0]

    # Add item functions.

    def _add_item(self, context, table, item):
        fields = item.keys()
        values = item.values()
        sql = "INSERT INTO %s (" % (table,) + ", ".join(fields) + ") VALUES (" \
          + ", ".join(["%s" for I in xrange(len(fields))]) + ")"
        self.log.debug(sql % tuple(values))
        context.cursor.execute(sql, tuple(values))

    def add_download(self, context, download):
        self._add_item(context, 'download', download)

    def add_architecture(self, context, architecture):
        self._add_item(context, 'architecture', architecture)

    def add_platform(self, context, platform):
        self._add_item(context, 'platform', platform)

    def add_type(self, context, type):
        self._add_item(context, 'download_type', type)

    # Edit item functions.

    def _edit_item(self, context, table, id, item):
        fields = item.keys()
        values = item.values()
        sql = "UPDATE %s SET " % (table,) + ", ".join([("%s = %%s" % (field))
          for field in fields]) + " WHERE id = %s"
        self.log.debug(sql % tuple(values + [id]))
        context.cursor.execute(sql, tuple(values + [id]))

    def edit_download(self, context, id, download):
        self._edit_item(context, 'download', id, download)

    def edit_architecture(self, context, id, architecture):
        self._edit_item(context, 'architecture', id, architecture)

    def edit_platform(self, context, id, platform):
        self._edit_item(context, 'platform', id, platform)

    def edit_type(self, context, id, type):
        self._edit_item(context, 'download_type', id, type)

    def edit_description(self, context, description):
        sql = "UPDATE system SET value = %s WHERE name = 'downloads_description'"
        self.log.debug(sql % (description,))
        context.cursor.execute(sql, (description,))

    # Delete item functions.

    def _delete_item(self, context, table, id):
        sql = "DELETE FROM " + table + " WHERE id = %s"
        self.log.debug(sql % (id,))
        context.cursor.execute(sql, (id,))

    def _delete_item_ref(self, context, table, column, id):
        sql = "UPDATE " + table + " SET " + column + " = NULL WHERE " + column + " = %s"
        self.log.debug(sql % (id,))
        context.cursor.execute(sql, (id,))

    def delete_download(self, context, id):
        self._delete_item(context, 'download', id)

    def delete_architecture(self, context, id):
        self._delete_item(context, 'architecture', id)
        self._delete_item_ref(context, 'download', 'architecture', id)

    def delete_platform(self, context, id):
        self._delete_item(context, 'platform', id)
        self._delete_item_ref(context, 'download', 'platform', id)

    def delete_type(self, context, id):
        self._delete_item(context, 'download_type', id)
        self._delete_item_ref(context, 'download', 'type', id)

    # Misc database access functions.

    def _get_attribute(self, context, table, column, where = '', values = ()):
        sql = 'SELECT ' + column + ' FROM ' + table + (where and (' WHERE ' +
          where) or '')
        self.log.debug(sql % values)
        context.cursor.execute(sql, values)
        for row in context.cursor:
            return row[0]
        return None

    def get_download_id_from_file(self, context, file):
        return self._get_attribute(context, 'download', 'file', 'id = %s',
          (file,))

    def get_number_of_downloads(self, context, download_ids = None):
        sql = 'SELECT SUM(count) FROM download' + (download_ids and
          (' WHERE id in (' + ', '.join([to_unicode(download_id) for download_id
          in download_ids]) + ')') or '')
        self.log.debug(sql)
        context.cursor.execute(sql)
        for row in context.cursor:
            return row[0]
        return None

    # Proces request functions.

    def process_downloads(self, context):
        # Clear data for next request.
        self.data = {}

        # Get database access.
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()

        # Get request mode
        modes = self._get_modes(context)
        self.log.debug('modes: %s' % modes)

        # Perform mode actions
        self._do_actions(context, modes)

        # Fill up the template data.
        self.data['authname'] = context.req.authname
        self.data['time'] = format_datetime(datetime.now(utc))
        self.data['realm'] = context.resource.realm

        # Add CSS styles
        add_stylesheet(context.req, 'common/css/wiki.css')
        add_stylesheet(context.req, 'downloads/css/downloads.css')
        add_stylesheet(context.req, 'downloads/css/admin.css')

        # Add JavaScripts
        add_script(context.req, 'common/js/trac.js')
        add_script(context.req, 'common/js/wikitoolbar.js')

        # Commit database changes and return template and data.
        db.commit()
        self.env.log.debug('data: %s' % (self.data,))
        return modes[-1] + '.html', {'downloads' : self.data}

    # Internal functions.

    def _get_modes(self, context):
        # Get request arguments.
        page = context.req.args.get('page')
        action = context.req.args.get('action')
        self.log.debug('context: %s page: %s action: %s' % (context, page,
          action))

        # Determine mode.
        if context.resource.realm == 'downloads-admin':
            if page == 'downloads':
                if action == 'post-add':
                    return ['downloads-post-add', 'admin-downloads-list']
                elif action == 'post-edit':
                    return ['downloads-post-edit', 'admin-downloads-list']
                elif action == 'delete':
                    return ['downloads-delete', 'admin-downloads-list']
                else:
                    return ['admin-downloads-list']
            elif page == 'architectures':
                if action == 'post-add':
                    return ['architectures-post-add', 'admin-architectures-list']
                elif action == 'post-edit':
                    return ['architectures-post-edit', 'admin-architectures-list']
                elif action == 'delete':
                    return ['architectures-delete', 'admin-architectures-list']
                else:
                    return ['admin-architectures-list']
            elif page == 'platforms':
                if action == 'post-add':
                    return ['platforms-post-add', 'admin-platforms-list']
                elif action == 'post-edit':
                    return ['platforms-post-edit', 'admin-platforms-list']
                elif action == 'delete':
                    return ['platforms-delete', 'admin-platforms-list']
                else:
                    return ['admin-platforms-list']
            elif page == 'types':
                if action == 'post-add':
                    return ['types-post-add', 'admin-types-list']
                elif action == 'post-edit':
                    return ['types-post-edit', 'admin-types-list']
                elif action == 'delete':
                    return ['types-delete', 'admin-types-list']
                else:
                    return ['admin-types-list']
        elif context.resource.realm  == 'downloads-core':
            if action == 'get-file':
                return ['get-file']
        elif context.resource.realm == 'downloads-downloads':
            if action == 'post-add':
                return ['downloads-post-add', 'downloads-list']
            elif action == 'edit':
                return ['description-edit', 'downloads-list']
            elif action == 'post-edit':
                return ['description-post-edit', 'downloads-list']
            else:
                return ['downloads-list']
        else:
            pass

    def _do_actions(self, context, actions):
        for action in actions:
            if action == 'get-file':
                context.req.perm.require('DOWNLOADS_VIEW')

                # Get request arguments.
                download_id = context.req.args.get('id') or 0
                download_file = context.req.args.get('file')

                # Get download.
                if download_id:
                    download = self.get_download(context, download_id)
                else:
                    download = self.get_download_by_file(context, download_file)

                # Check if requested download exists.
                if not download:
                    raise TracError('File not found.')

                # Check resource based permission.
                context.req.perm.require('DOWNLOADS_VIEW',
                  Resource('downloads', download['id']))

                # Get download file path.
                path = os.path.normpath(os.path.join(self.path, to_unicode(
                  download['id']), download['file']))
                self.log.debug('path: %s' % (path,))

                # Increase downloads count.
                new_download = {'count' : download['count'] + 1}

                # Edit download.
                self.edit_download(context, download['id'], new_download)

                # Notify change listeners.
                for listener in self.change_listeners:
                    listener.download_changed(context, new_download,
                      download)

                # Commit DB before file send.
                db = self.env.get_db_cnx()
                db.commit()

                # Guess mime type.
                file = open(path.encode('utf-8'), "r")
                file_data = file.read(1000)
                file.close()
                mimeview = Mimeview(self.env)
                mime_type = mimeview.get_mimetype(path, file_data)
                if not mime_type:
                    mime_type = 'application/octet-stream'
                if 'charset=' not in mime_type:
                    charset = mimeview.get_charset(file_data, mime_type)
                    mime_type = mime_type + '; charset=' + charset

                # Return uploaded file to request.
                context.req.send_header('Content-Disposition',
                  'attachment;filename="%s"' % (os.path.normpath(
                  download['file'])))
                context.req.send_header('Content-Description',
                  download['description'])
                context.req.send_file(path.encode('utf-8'), mime_type)

            elif action == 'downloads-list':
                context.req.perm.require('DOWNLOADS_VIEW')

                self.log.debug('visible_fields: %s' % (self.visible_fields,))

                # Get form values.
                order = context.req.args.get('order') or self.download_sort
                if context.req.args.has_key('desc'):
                    desc = context.req.args.get('desc') == '1'
                else:
                    desc = self.download_sort_direction

                self.data['order'] = order
                self.data['desc'] = desc
                self.data['has_tags'] = self.env.is_component_enabled(
                  'tractags.api.TagEngine')
                self.data['visible_fields'] = self.visible_fields
                self.data['title'] = self.title
                self.data['description'] = self.get_description(context)
                self.data['downloads'] = self.get_downloads(context, order,
                  desc)
                self.data['visible_fields'] = [visible_field for visible_field
                  in self.visible_fields]

                # Component, versions, etc. are needed only for new download
                # add form.
                if context.req.perm.has_permission('DOWNLOADS_ADD'):
                    self.data['components'] = self.get_components(context)
                    self.data['versions'] = self.get_versions(context)
                    self.data['architectures'] = self.get_architectures(context)
                    self.data['platforms'] = self.get_platforms(context)
                    self.data['types'] = self.get_types(context)

            elif action == 'admin-downloads-list':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values
                order = context.req.args.get('order') or self.download_sort
                if context.req.args.has_key('desc'):
                    desc = context.req.args.get('desc') == '1'
                else:
                    desc = self.download_sort_direction
                download_id = int(context.req.args.get('download') or 0)

                self.data['order'] = order
                self.data['desc'] = desc
                self.data['has_tags'] = self.env.is_component_enabled(
                  'tractags.api.TagEngine')
                self.data['download'] = self.get_download(context,
                  download_id)
                self.data['downloads'] = self.get_downloads(context,
                  order, desc)
                self.data['components'] = self.get_components(context)
                self.data['versions'] = self.get_versions(context)
                self.data['architectures'] = self.get_architectures(context)
                self.data['platforms'] = self.get_platforms(context)
                self.data['types'] = self.get_types(context)

            elif action == 'description-edit':
                context.req.perm.require('DOWNLOADS_ADMIN')

            elif action == 'description-post-edit':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values.
                description = context.req.args.get('description')

                # Set new description.
                self.edit_description(context, description)

            elif action == 'downloads-post-add':
                context.req.perm.require('DOWNLOADS_ADD')

                # Get form values.
                file, filename, file_size = self._get_file_from_req(context)
                download = {'file' : filename,
                            'description' : context.req.args.get('description'),
                            'size' : file_size,
                            'time' : to_timestamp(datetime.now(utc)),
                            'count' : 0,
                            'author' : context.req.authname,
                            'tags' : context.req.args.get('tags'),
                            'component' : context.req.args.get('component'),
                            'version' : context.req.args.get('version'),
                            'architecture' : context.req.args.get('architecture'),
                            'platform' : context.req.args.get('platform'),
                            'type' : context.req.args.get('type')}

                # Upload file to DB and file storage.
                self._add_download(context, download, file)

                # Close input file.
                file.close()

            elif action == 'downloads-post-edit':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values.
                download_id = context.req.args.get('id')
                old_download = self.get_download(context, download_id)
                download = {'description' : context.req.args.get('description'),
                            'tags' : context.req.args.get('tags'),
                            'component' : context.req.args.get('component'),
                            'version' : context.req.args.get('version'),
                            'architecture' : context.req.args.get('architecture'),
                            'platform' : context.req.args.get('platform'),
                            'type' : context.req.args.get('type')}

                # Edit Download.
                self.edit_download(context, download_id, download)

                # Notify change listeners.
                for listener in self.change_listeners:
                    listener.download_changed(context, download, old_download)

            elif action == 'downloads-delete':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get selected downloads.
                selection = context.req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete download.
                if selection:
                    for download_id in selection:
                        download = self.get_download(context, download_id)
                        self.log.debug('download: %s' % (download,))
                        self._delete_download(context, download)

            elif action == 'admin-architectures-list':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values
                order = context.req.args.get('order') or self.architecture_sort
                if context.req.args.has_key('desc'):
                    desc = context.req.args.get('desc') == '1'
                else:
                    desc = self.architecture_sort_direction
                architecture_id = int(context.req.args.get('architecture') or 0)

                # Display architectures.
                self.data['order'] = order
                self.data['desc'] = desc
                self.data['architecture'] = self.get_architecture(context,
                  architecture_id)
                self.data['architectures'] = self.get_architectures(context,
                  order, desc)

            elif action == 'architectures-post-add':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values.
                architecture = {'name' : context.req.args.get('name'),
                                'description' : context.req.args.get('description')}

                # Add architecture.
                self.add_architecture(context, architecture)

            elif action == 'architectures-post-edit':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values.
                architecture_id = context.req.args.get('id')
                architecture = {'name' : context.req.args.get('name'),
                                'description' : context.req.args.get('description')}

                # Add architecture.
                self.edit_architecture(context, architecture_id, architecture)

            elif action == 'architectures-delete':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get selected architectures.
                selection = context.req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete architectures.
                if selection:
                    for architecture_id in selection:
                        self.delete_architecture(context, architecture_id)

            elif action == 'admin-platforms-list':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values.
                order = context.req.args.get('order') or self.platform_sort
                if context.req.args.has_key('desc'):
                    desc = context.req.args.get('desc') == '1'
                else:
                    desc = self.platform_sort_direction
                platform_id = int(context.req.args.get('platform') or 0)

                # Display platforms.
                self.data['order'] = order
                self.data['desc'] = desc
                self.data['platform'] = self.get_platform(context,
                  platform_id)
                self.data['platforms'] = self.get_platforms(context, order,
                  desc)

            elif action == 'platforms-post-add':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values.
                platform = {'name' : context.req.args.get('name'),
                            'description' : context.req.args.get('description')}

                # Add platform.
                self.add_platform(context, platform)

            elif action == 'platforms-post-edit':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values.
                platform_id = context.req.args.get('id')
                platform = {'name' : context.req.args.get('name'),
                            'description' : context.req.args.get('description')}

                # Add platform.
                self.edit_platform(context, platform_id, platform)

            elif action == 'platforms-delete':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get selected platforms.
                selection = context.req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete platforms.
                if selection:
                    for platform_id in selection:
                        self.delete_platform(context, platform_id)

            elif action == 'admin-types-list':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values
                order = context.req.args.get('order') or self.type_sort
                if context.req.args.has_key('desc'):
                    desc = context.req.args.get('desc') == '1'
                else:
                    desc = self.type_sort_direction
                platform_id = int(context.req.args.get('type') or 0)

                # Display platforms.
                self.data['order'] = order
                self.data['desc'] = desc
                self.data['type'] = self.get_type(context, platform_id)
                self.data['types'] = self.get_types(context, order, desc)

            elif action == 'types-post-add':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values.
                type = {'name' : context.req.args.get('name'),
                        'description' : context.req.args.get('description')}

                # Add type.
                self.add_type(context, type)

            elif action == 'types-post-edit':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get form values.
                type_id = context.req.args.get('id')
                type = {'name' : context.req.args.get('name'),
                        'description' : context.req.args.get('description')}

                # Add platform.
                self.edit_type(context, type_id, type)

            elif action == 'types-delete':
                context.req.perm.require('DOWNLOADS_ADMIN')

                # Get selected types.
                selection = context.req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete types.
                if selection:
                    for type_id in selection:
                        self.delete_type(context, type_id)

    """ Full implementation of download addition. It creates DB entry for
    download <download> and stores download file <file> to file system. """
    def _add_download(self, context, download, file):
        # Check for file name uniqueness.
        if self.unique_filename:
            if self.get_download_by_file(context, download['file']):
                raise TracError('File with same name is already uploaded and'
                  ' unique file names are enabled.')

        # Check correct file type.
        name, ext = os.path.splitext(download['file'])
        self.log.debug('file_ext: %s ext: %s' % (ext, self.ext))
        if not (ext[1:].lower() in self.ext) and not ('all' in self.ext):
            raise TracError('Unsupported file type.')

        # Check for maximum file size.
        if self.max_size >= 0 and download['size'] > self.max_size:
            raise TracError('Maximum file size: %s bytes' % (self.max_size),
              'Upload failed')

        # Add new download to DB.
        self.add_download(context, download)

        # Get inserted download by time to get its ID.
        download = self.get_download_by_time(context, download['time'])

        # Prepare file paths.
        path = os.path.normpath(os.path.join(self.path, to_unicode(
          download['id'])))
        filepath = os.path.normpath(os.path.join(path, download['file']))

        self.log.debug('path: %s' % ((path,)))
        self.log.debug('filepath: %s' % ((filepath,)))

        # Store uploaded image.
        try:
            os.mkdir(path.encode('utf-8'))
            out_file = open(filepath.encode('utf-8'), "wb+")
            file.seek(0)
            shutil.copyfileobj(file, out_file)
            out_file.close()
        except Exception, error:
            self.delete_download(context, download['id'])
            self.log.debug(error)
            try:
                os.remove(filepath.encode('utf-8'))
            except:
                pass
            try:
                os.rmdir(path.encode('utf-8'))
            except:
                pass
            raise TracError('Error storing file %s! Is directory specified in' \
              ' path config option in [downloads] section of trac.ini' \
              ' existing?' % (download['file'],))

        # Notify change listeners.
        for listener in self.change_listeners:
            listener.download_created(context, download)

    def _delete_download(self, context, download):
        try:
            self.delete_download(context, download['id'])
            path = os.path.join(self.path, to_unicode(download['id']))
            filepath = os.path.join(path, download['file'])
            path = os.path.normpath(path)
            filepath = os.path.normpath(filepath)
            os.remove(filepath)
            os.rmdir(path)

            # Notify change listeners.
            for listener in self.change_listeners:
                listener.download_deleted(context, download)
        except:
            pass

    def _get_file_from_req(self, context):
        file = context.req.args['file']

        # Test if file is uploaded.
        if not hasattr(file, 'filename') or not file.filename:
            raise TracError('No file uploaded.')

        # Get file size.
        if hasattr(file.file, 'fileno'):
            size = os.fstat(file.file.fileno())[6]
        else:
            # Seek to end of file to get its size.
            file.file.seek(0, 2)
            size = file.file.tell()
            file.file.seek(0)
        if size == 0:
            raise TracError('Can\'t upload empty file.')

        # Try to normalize the filename to unicode NFC if we can.
        # Files uploaded from OS X might be in NFD.
        self.log.debug('input filename: %s', (file.filename,))
        filename = unicodedata.normalize('NFC', to_unicode(file.filename,
          'utf-8'))
        filename = filename.replace('\\', '/').replace(':', '/')
        filename = os.path.basename(filename)
        self.log.debug('output filename: %s', (filename,))

        return file.file, filename, size
