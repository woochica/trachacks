# -*- coding: utf-8 -*-

import os, shutil, re, mimetypes, unicodedata
from datetime import *

from trac.core import *
from trac.config import Option, BoolOption
from trac.web.chrome import add_stylesheet, add_script
from trac.util.datefmt import to_timestamp, to_datetime, utc, \
  format_datetime, pretty_timedelta
from trac.util.text import to_unicode, unicode_unquote, unicode_quote, \
  pretty_size


class IDownloadChangeListener(Interface):
    """Extension point interface for components that require notification
    when downloads are created, modified, or deleted."""

    def download_created(req, download):
        """Called when a download is created. Only argument `download` is
        a dictionary with download field values."""

    def download_changed(req, download, old_download):
        """Called when a download is modified.
        `old_download` is a dictionary containing the previous values of the
        fields and `download` is a dictionary with new values. """

    def download_deleted(req, download):
        """Called when a download is deleted. `download` argument is
        a dictionary with values of fields of just deleted download."""

class DownloadsApi(Component):

    # List of all field of downloads table.
    all_fields = ['id', 'file', 'description', 'size', 'time', 'count', 'author',
      'tags', 'component', 'version', 'architecture', 'platform', 'type']

    # Download change listeners.
    change_listeners = ExtensionPoint(IDownloadChangeListener)

    # Configuration options.
    title = Option('downloads', 'title', 'Downloads',
      'Main navigation bar button title.')
    path = Option('downloads', 'path', '/var/lib/trac/downloads',
      'Directory to store uploaded downloads.')
    ext = Option('downloads', 'ext', 'zip gz bz2 rar',
      'List of file extensions allowed to upload.')
    visible_fields = Option('downloads', 'visible_fields',
      ' '.join(all_fields), 'List of downloads table fields that should'
      ' be visible to users on Downloads section.')
    unique_filename = BoolOption('downloads', 'unique_filename', False,
      'If enabled checks if uploaded file has unique name.')

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
        # Get versions from table.
        versions = self._get_items(context, 'version', ('name', 'description'),
          order_by = order_by, desc = desc)

        # Add IDs to versions according to selected sorting.
        id = 0
        for version in versions:
            id = id + 1
            version['id'] = id
        return versions

    def get_components(self, context, order_by = '', desc = False):
        # Get components from table.
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

    def get_visible_fields(self):
        # Get list of enabled fields from config option.
        visible_fields = self.visible_fields.split(' ')

        # Construct dictionary of visible_fields.
        fields = {}
        for field in self.all_fields:
            fields[field] = field in visible_fields
        return fields

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
        return self._get_item(context, 'architecture', ('id', 'name',
          'description'), 'id = %s', (id,))

    def get_platform(self, context, id):
        return self._get_item(context, 'platform', ('id', 'name',
          'description'), 'id = %s', (id,))

    def get_type(self, context, id):
        return self._get_item(context, 'download_type', ('id', 'name',
          'description'), 'id = %s', (id,))

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
        self._do_action(context, modes)

        # Fill up HDF structure and return template
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
        self.env.log.debug(self.data)
        return modes[-1] + '.html', {'downloads' : self.data}

    # Internal functions.

    def _get_modes(self, context):
        # Get request arguments.
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
            elif action == 'edit':
                return ['description-edit', 'downloads-list']
            elif action == 'post-edit':
                return ['description-post-edit', 'downloads-list']
            else:
                return ['downloads-list']
        else:
            pass

    def _do_action(self, context, modes):
        for mode in modes:
            if mode == 'get-file':
                context.req.perm.assert_permission('DOWNLOADS_VIEW')

                # Get form values.
                download_id = context.req.args.get('id') or 0
                download_file = context.req.args.get('file')

                # Get download.
                if download_id:
                    download = self.get_download(context, download_id)
                else:
                    download = self.get_download_by_file(context, download_file)

                if download:
                    path = os.path.join(self.path, to_unicode(download['id']),
                      download['file'])
                    path = os.path.normpath(path)
                    self.log.debug('path: %s' % (path,))

                    # Increase downloads count.
                    new_download = {'count' : download['count'] + 1}

                    # Edit download.
                    self.edit_download(context, download['id'], new_download)

                    # Notify change listeners.
                    for listener in self.change_listeners:
                        listener.download_changed(context.req, new_download,
                          download)

                    # Commit DB before file send.
                    db = self.env.get_db_cnx()
                    db.commit()

                    # Return uploaded file to request.
                    self.log.debug(download['file'])
                    context.req.send_header('Content-Disposition',
                      'attachment;filename=%s' % (download['file']))
                    context.req.send_header('Content-Description',
                      download['description'])
                    context.req.send_file(path, mimetypes.guess_type(path)[0])
                else:
                    raise TracError('File not found.')

            elif mode == 'downloads-list':
                context.req.perm.assert_permission('DOWNLOADS_VIEW')

                # Get form values.
                order = context.req.args.get('order') or 'id'
                desc = context.req.args.get('desc')

                self.data['order'] = order
                self.data['desc'] = desc
                self.data['has_tags'] = self.env.is_component_enabled(
                  'tractags.api.TagEngine')
                self.data['title'] = self.title
                self.data['description'] = self.get_description(context)
                self.data['downloads'] = self.get_downloads(context, order,
                  desc)
                self.data['visible_fields'] = self.get_visible_fields()

            elif mode == 'admin-downloads-list':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values
                order = context.req.args.get('order') or 'id'
                desc = context.req.args.get('desc')
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

            elif mode == 'description-edit':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

            elif mode == 'description-post-edit':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                description = context.req.args.get('description')

                # Set new description.
                self.edit_description(context, description)

            elif mode == 'downloads-post-add':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

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

                # Check for file name uniqueness.
                if self.unique_filename:
                    if self.get_download_by_file(context, filename):
                        raise TracError('File with same name is already' \
                          ' uploaded and unique file names are enabled.')

                # Add new download.
                self.add_download(context, download)

                # Get inserted download.
                download = self.get_download_by_time(context, download['time'])

                # Check correct file type.
                if not 'all' in self.ext:
                    name, ext = os.path.splitext(download['file'])
                    self.log.debug('file_ext: %s ext: %s' % (ext, self.ext))
                    if not ext[1:].lower() in self.ext:
                        raise TracError('Unsupported uploaded file type.')
                else:
                    raise TracError('Unsupported uploaded file type.')

                # Prepare file paths
                path = os.path.join(self.path, unicode(download['id']))
                filepath = os.path.join(path, download['file'])
                path = os.path.normpath(path)
                filepath = os.path.normpath(filepath)
                self.log.debug('filepath: %s' % ((filepath,)))
                self.log.debug('path: %s' % ((path,)))

                # Notify change listeners.
                for listener in self.change_listeners:
                    listener.download_created(context.req, download)

                # Store uploaded image.
                try:
                    os.mkdir(path)
                    out_file = open(filepath, "wb+")
                    shutil.copyfileobj(file, out_file)
                    out_file.close()
                except Exception, error:
                    self.log.debug(error)
                    self.delete_download(context, download['id'])
                    try:
                        os.remove(filepath)
                    except:
                        pass
                    try:
                        os.rmdir(path)
                    except:
                        pass
                    raise TracError('Error storing file %s! Is directory' \
                      ' specified in path config option in [downloads] section' \
                      ' of trac.ini existing?' % (download['file'],))

            elif mode == 'downloads-post-edit':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

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
                    listener.download_changed(context.req, download,
                      old_download)

            elif mode == 'downloads-delete':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get selected downloads.
                selection = context.req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete download.
                if selection:
                    for download_id in selection:
                        download = self.get_download(context, download_id)
                        self.log.debug(download)

                        try:
                            self.delete_download(context, download['id'])
                            path = os.path.join(self.path,
                              to_unicode(download['id']))
                            filepath = os.path.join(path, download['file'])
                            path = os.path.normpath(path)
                            filepath = os.path.normpath(filepath)
                            os.remove(filepath)
                            os.rmdir(path)

                            # Notify change listeners.
                            for listener in self.change_listeners:
                                listener.download_deleted(context.req, download)
                        except:
                            pass

            elif mode == 'admin-architectures-list':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values
                order = context.req.args.get('order') or 'id'
                desc = context.req.args.get('desc')
                architecture_id = int(context.req.args.get('architecture') or 0)

                # Display architectures.
                self.data['order'] = order
                self.data['desc'] = desc
                self.data['architecture'] = self.get_architecture(context,
                  architecture_id)
                self.data['architectures'] = self.get_architectures(context,
                  order, desc)

            elif mode == 'architectures-post-add':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                architecture = {'name' : context.req.args.get('name'),
                                'description' : context.req.args.get('description')}

                # Add architecture.
                self.add_architecture(context, architecture)

            elif mode == 'architectures-post-edit':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                architecture_id = context.req.args.get('id')
                architecture = {'name' : context.req.args.get('name'),
                                'description' : context.req.args.get('description')}

                # Add architecture.
                self.edit_architecture(context, architecture_id, architecture)

            elif mode == 'architectures-delete':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get selected architectures.
                selection = context.req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete architectures.
                if selection:
                    for architecture_id in selection:
                        self.delete_architecture(context, architecture_id)

            elif mode == 'admin-platforms-list':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                order = context.req.args.get('order') or 'id'
                desc = context.req.args.get('desc')
                platform_id = int(context.req.args.get('platform') or 0)

                # Display platforms.
                self.data['order'] = order
                self.data['desc'] = desc
                self.data['platform'] = self.get_platform(context,
                  platform_id)
                self.data['platforms'] = self.get_platforms(context, order,
                  desc)

            elif mode == 'platforms-post-add':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                platform = {'name' : context.req.args.get('name'),
                            'description' : context.req.args.get('description')}

                # Add platform.
                self.add_platform(context, platform)

            elif mode == 'platforms-post-edit':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                platform_id = context.req.args.get('id')
                platform = {'name' : context.req.args.get('name'),
                            'description' : context.req.args.get('description')}

                # Add platform.
                self.edit_platform(context, platform_id, platform)

            elif mode == 'platforms-delete':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get selected platforms.
                selection = context.req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete platforms.
                if selection:
                    for platform_id in selection:
                        self.delete_platform(context, platform_id)

            elif mode == 'admin-types-list':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values
                order = context.req.args.get('order') or 'id'
                desc = context.req.args.get('desc')
                platform_id = int(context.req.args.get('type') or 0)

                # Display platforms.
                self.data['order'] = order
                self.data['desc'] = desc
                self.data['type'] = self.get_type(context, platform_id)
                self.data['types'] = self.get_types(context, order, desc)

            elif mode == 'types-post-add':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                type = {'name' : context.req.args.get('name'),
                        'description' : context.req.args.get('description')}

                # Add type.
                self.add_type(context, type)

            elif mode == 'types-post-edit':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                type_id = context.req.args.get('id')
                type = {'name' : context.req.args.get('name'),
                        'description' : context.req.args.get('description')}

                # Add platform.
                self.edit_type(context, type_id, type)

            elif mode == 'types-delete':
                context.req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get selected types.
                selection = context.req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete types.
                if selection:
                    for type_id in selection:
                        self.delete_type(context, type_id)

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
