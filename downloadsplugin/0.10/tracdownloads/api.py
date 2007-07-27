import os, time, re, mimetypes

from trac.core import *
from trac.config import Option
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.util import format_datetime, pretty_timedelta, pretty_size
from trac.web.chrome import add_stylesheet, add_script

class IDownloadChangeListener(Interface):
    """Extension point interface for components that require notification
    when downloads are created, modified, or deleted."""

    def download_created(download):
        """Called when a download is created. Only argument `download` is
        a dictionary with download field values."""

    def download_changed(download, old_download):
        """Called when a download is modified.
        `old_download` is a dictionary containing the previous values of the
        fields and `download` is a dictionary with new values. """

    def download_deleted(download):
        """Called when a download is deleted. `download` argument is
        a dictionary with values of fields of just deleted download."""

class DownloadsApi(Component):

    title = Option('downloads', 'title', 'Downloads',
      'Main navigation bar button title.')
    path = Option('downloads', 'path', '/var/lib/trac/downloads',
      'Directory to store uploaded downloads.')
    ext = Option('downloads', 'ext', 'zip gz bz2 rar',
      'List of file extensions allowed to upload.')

    # Get list functions.

    def get_versions(self, req, cursor):
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

    def get_components(self, req, cursor):
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

    def get_downloads(self, req, cursor, order_by = 'id', desc = False):
        columns = ('id', 'file', 'description', 'size', 'time', 'count',
          'author', 'tags', 'component', 'version', 'architecture', 'platform',
          'type')
        sql = "SELECT id, file, description, size, time, count, author, tags," \
          " component, version, architecture, platform, type FROM download " \
          "ORDER BY " + order_by + (" ASC", " DESC")[bool(desc)]
        self.log.debug(sql)
        cursor.execute(sql)
        downloads = []
        for row in cursor:
            row = dict(zip(columns, row))
            row['description'] = wiki_to_oneliner(row['description'], self.env)
            row['size'] = pretty_size(row['size'])
            row['time'] = pretty_timedelta(row['time'])
            row['count'] = row['count'] or 0
            downloads.append(row)

        # Replace field ids with apropriate objects.
        for download in downloads:
            download['architecture'] = self.get_architecture(cursor,
              download['architecture'])
            download['platform'] = self.get_platform(cursor,
              download['platform'])
            download['type'] = self.get_type(cursor, download['type'])
        return downloads

    def get_architectures(self, req, cursor, order_by = 'id', desc = False):
        columns = ('id', 'name', 'description')
        sql = "SELECT id, name, description FROM architecture ORDER BY " + \
          order_by + (" ASC", " DESC")[bool(desc)]
        self.log.debug(sql)
        cursor.execute(sql)
        architectures = []
        for row in cursor:
            row = dict(zip(columns, row))
            row['description'] = wiki_to_oneliner(row['description'],
              self.env)
            architectures.append(row)
        return architectures

    def get_platforms(self, req, cursor, order_by = 'id', desc = False):
        columns = ('id', 'name', 'description')
        sql = "SELECT id, name, description FROM platform ORDER BY " + \
          order_by + (" ASC", " DESC")[bool(desc)]
        self.log.debug(sql)
        cursor.execute(sql)
        platforms = []
        for row in cursor:
            row = dict(zip(columns, row))
            row['description'] = wiki_to_oneliner(row['description'],
              self.env)
            platforms.append(row)
        return platforms

    def get_types(self, req, cursor, order_by = 'id', desc = False):
        columns = ('id', 'name', 'description')
        sql = "SELECT id, name, description FROM download_type ORDER BY " + \
          order_by + (" ASC", " DESC")[bool(desc)]
        self.log.debug(sql)
        cursor.execute(sql)
        types = []
        for row in cursor:
            row = dict(zip(columns, row))
            row['description'] = wiki_to_oneliner(row['description'],
              self.env)
            types.append(row)
        return types

    # Get one item functions.

    def get_download(self, cursor, id):
        columns = ('id', 'file', 'description', 'size', 'time', 'count',
          'author', 'tags', 'component', 'version', 'architecture', 'platform',
          'type')
        sql = "SELECT id, file, description, size, time, count, author, tags," \
          " component, version, architecture, platform, type FROM download" \
          " WHERE id = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))
        for row in cursor:
            row = dict(zip(columns, row))
            row['count'] = row['count'] or 0
            return row

    def get_download_by_time(self, cursor, time):
        columns = ('id', 'file', 'description', 'size', 'time', 'count',
          'author', 'tags', 'component', 'version', 'architecture', 'platform',
          'type')
        sql = "SELECT id, file, description, size, time, count, author, tags," \
          " component, version, architecture, platform, type FROM download" \
          " WHERE time = %s"
        self.log.debug(sql % (time,))
        cursor.execute(sql, (time,))
        for row in cursor:
            row = dict(zip(columns, row))
            row['count'] = row['count'] or 0
            return row

    def get_architecture(self, cursor, id):
        columns = ('id', 'name', 'description')
        sql = "SELECT id, name, description FROM architecture WHERE id = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))
        for row in cursor:
            row = dict(zip(columns, row))
            return row

    def get_platform(self, cursor, id):
        columns = ('id', 'name', 'description')
        sql = "SELECT id, name, description FROM platform WHERE id = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))
        for row in cursor:
            row = dict(zip(columns, row))
            return row

    def get_type(self, cursor, id):
        columns = ('id', 'name', 'description')
        sql = "SELECT id, name, description FROM download_type WHERE id = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))
        for row in cursor:
            row = dict(zip(columns, row))
            return row

    def get_description(self, req, cursor):
        sql = "SELECT value FROM system WHERE name = 'downloads_description'"
        self.log.debug(sql)
        cursor.execute(sql)
        for row in cursor:
            return (row[0], wiki_to_html(row[0], self.env, req))

    # Add item functions.

    def _add_item(self, cursor, table, item):
        fields = item.keys()
        values = item.values()
        sql = "INSERT INTO %s (" % (table,) + ", ".join(fields) + ") VALUES (" \
          + ", ".join(["%s" for I in xrange(len(fields))]) + ")"
        self.log.debug(sql % tuple(values))
        cursor.execute(sql, tuple(values))

    def add_download(self, cursor, download):
        self._add_item(cursor, 'download', download)

    def add_architecture(self, cursor, architecture):
        self._add_item(cursor, 'architecture', architecture)

    def add_platform(self, cursor, platform):
        self._add_item(cursor, 'platform', platform)

    def add_type(self, cursor, type):
        self._add_item(cursor, 'download_type', type)

    # Edit item functions.

    def _edit_item(self, cursor, table, id, item):
        fields = item.keys()
        values = item.values()
        sql = "UPDATE %s SET " % (table,) + ", ".join([("%s = %%s" % (field))
          for field in fields]) + " WHERE id = %s"
        self.log.debug(sql % tuple(values + [id]))
        cursor.execute(sql, tuple(values + [id]))

    def edit_download(self, cursor, id, download):
        self._edit_item(cursor, 'download', id, download)

    def edit_architecture(self, cursor, id, architecture):
        self._edit_item(cursor, 'architecture', id, architecture)

    def edit_platform(self, cursor, id, platform):
        self._edit_item(cursor, 'platform', id, platform)

    def edit_type(self, cursor, id, type):
        self._edit_item(cursor, 'download_type', id, type)

    def edit_description(self, cursor, description):
        sql = "UPDATE system SET value = %s WHERE name = 'downloads_description'"
        self.log.debug(sql % (description,))
        cursor.execute(sql, (description,))

    # Delete item functions.

    def _delete_item(self, cursor, table, id):
        sql = "DELETE FROM " + table + " WHERE id = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))

    def _delete_item_ref(self, cursor, table, column, id):
        sql = "UPDATE " + table + " SET " + column + " = NULL WHERE " + column + " = %s"
        self.log.debug(sql % (id,))
        cursor.execute(sql, (id,))

    def delete_download(self, cursor, id):
        self._delete_item(cursor, 'download', id)

    def delete_architecture(self, cursor, id):
        self._delete_item(cursor, 'architecture', id)
        self._delete_item_ref(cursor, 'download', 'architecture', id)

    def delete_platform(self, cursor, id):
        self._delete_item(cursor, 'platform', id)
        self._delete_item_ref(cursor, 'download', 'platform', id)

    def delete_type(self, cursor, id):
        self._delete_item(cursor, 'download_type', id)
        self._delete_item_ref(cursor, 'download', 'type', id)

    # Proces request functions.

    def process_downloads(self, req, cursor):
        # Get request mode
        modes = self._get_modes(req)
        self.log.debug('modes: %s' % modes)

        # Perform mode actions
        self._do_action(req, cursor, modes)

        # Add CSS styles
        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'downloads/css/downloads.css')
        add_stylesheet(req, 'downloads/css/admin.css')

        # Add JavaScripts
        add_script(req, 'common/js/trac.js')
        add_script(req, 'common/js/wikitoolbar.js')

        # Fill up HDF structure and return template
        req.hdf['download.authname'] = req.authname
        req.hdf['download.time'] = format_datetime(time.time())
        return modes[-1] + '.cs', None

    # Internal functions.

    def _get_modes(self, req):
        # Get request arguments.
        context = req.args.get('context')
        page = req.args.get('page')
        action = req.args.get('action')
        self.log.debug('context: %s page: %s action: %s' % (context, page,
          action))

        if context == 'admin':
            req.hdf['downloads.href'] = req.href.admin('downloads', page)
        elif context == 'core':
            req.hdf['downloads.href'] = req.href.downloads()

        # Determine mode.
        if context == 'admin':
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
        elif context == 'core':
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

    def _do_action(self, req, cursor, modes):
        for mode in modes:
            if mode == 'get-file':
                req.perm.assert_permission('DOWNLOADS_VIEW')

                # Get form values.
                download_id = req.args.get('id')

                # Get download.
                download = self.get_download(cursor, download_id)

                if download:
                    path = os.path.join(self.path, unicode(download['id']),
                      download['file'])
                    self.log.debug('path: %s' % (path,))

                    # Increase downloads count.
                    db = self.env.get_db_cnx()
                    cursor = db.cursor()
                    self.edit_download(cursor, download['id'], {'count' :
                      download['count'] + 1})
                    db.commit()

                    # Return uploaded file to request.
                    type = mimetypes.guess_type(path)[0]
                    req.send_file(path, type)
                else:
                    raise TracError('File not found.')

            elif mode == 'downloads-list':
                req.perm.assert_permission('DOWNLOADS_VIEW')

                # Get form values.
                order = req.args.get('order') or 'id'
                desc = req.args.get('desc')

                req.hdf['downloads.order'] = order
                req.hdf['downloads.desc'] = desc
                req.hdf['downloads.has_tags'] = self.env.is_component_enabled(
                  'TagEngine')
                req.hdf['downloads.title'] = self.title
                req.hdf['downloads.description'] = self.get_description(req, cursor)
                req.hdf['downloads.downloads'] = self.get_downloads(req,
                  cursor, order, desc)

            elif mode == 'admin-downloads-list':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values
                order = req.args.get('order') or 'id'
                desc = req.args.get('desc')
                download_id = int(req.args.get('download') or 0)

                # Fill HDF structure
                req.hdf['downloads.order'] = order
                req.hdf['downloads.desc'] = desc
                req.hdf['downloads.has_tags'] = self.env.is_component_enabled(
                  'TagEngine')
                req.hdf['downloads.download'] = self.get_download(cursor,
                  download_id)
                req.hdf['downloads.downloads'] = self.get_downloads(req,
                  cursor, order, desc)
                req.hdf['downloads.components'] = self.get_components(req,
                  cursor)
                req.hdf['downloads.versions'] = self.get_versions(req, cursor)
                req.hdf['downloads.architectures'] = self.get_architectures(
                  req, cursor)
                req.hdf['downloads.platforms'] = self.get_platforms(req,
                  cursor)
                req.hdf['downloads.types'] = self.get_types(req, cursor)

            elif mode == 'description-edit':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

            elif mode == 'description-post-edit':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                description = req.args.get('description')

                # Set new description.
                self.edit_description(cursor, description)

            elif mode == 'downloads-post-add':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                file, file_name = self._get_file_from_req(req)
                file_content = file.read()
                download = {'file' : file_name,
                            'description' : req.args.get('description'),
                            'size' : len(file_content),
                            'time' : int(time.time()),
                            'author' : req.authname,
                            'tags' : req.args.get('tags'),
                            'component' : req.args.get('component'),
                            'version' : req.args.get('version'),
                            'architecture' : req.args.get('architecture'),
                            'platform' : req.args.get('platform'),
                            'type' : req.args.get('type')}

                # Add new download.
                self.add_download(cursor, download)

                # Get inserted download.
                download = self.get_download_by_time(cursor, download['time'])

                # Check correct file type.
                reg = re.compile(r'^(.*)[.](.*)$')
                result = reg.match(download['file'])
                self.log.debug('ext: %s' % (result.group(2)))
                if result:
                    if not result.group(2).lower() in self.ext.split(' '):
                        raise TracError('Unsupported uploaded file type.')
                else:
                    raise TracError('Unsupported uploaded file type.')

                # Prepare file paths
                path = os.path.join(self.path, str(download['id']))
                filepath = os.path.join(path, download['file'])
                self.log.debug('filepath: %s' % (filepath))

                # Store uploaded image.
                try:
                    os.mkdir(path)
                    out_file = open(filepath, "w+")
                    out_file.write(file_content)
                    out_file.close()

                    # Notify about change.
                    # TODO

                except:
                    self.api.delete_download(cursor, download['id'])
                    try:
                        os.remove(filepath)
                        os.rmdir(path)
                    except:
                        pass
                    raise TracError('Error storing file %s! Is directory specified' \
                      ' in path config option in [downloads] section of' \
                      ' trac.ini existing?' % (download['file']))

            elif mode == 'downloads-post-edit':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                download_id = req.args.get('id')
                download = {'description' : req.args.get('description'),
                            'tags' : req.args.get('tags'),
                            'component' : req.args.get('component'),
                            'version' : req.args.get('version'),
                            'architecture' : req.args.get('architecture'),
                            'platform' : req.args.get('platform'),
                            'type' : req.args.get('type')}

                # Edit Download.
                self.edit_download(cursor, download_id, download)

                # Notify about change.
                # TODO

            elif mode == 'downloads-delete':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get selected downloads.
                selection = req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete download.
                if selection:
                    for download_id in selection:
                        download = self.get_download(cursor, download_id)
                        self.log.debug(download)
                        try:
                            self.delete_download(cursor, download['id'])
                            path = os.path.join(self.path, unicode(download['id']))
                            os.remove(os.path.join(path, download['file']))
                            os.rmdir(path)

                            # Notify about change.
                            # TODO

                        except:
                            pass

            elif mode == 'admin-architectures-list':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values
                order = req.args.get('order') or 'id'
                desc = req.args.get('desc')
                architecture_id = int(req.args.get('architecture') or 0)

                # Display architectures.
                req.hdf['downloads.order'] = order
                req.hdf['downloads.desc'] = desc
                req.hdf['downloads.architecture'] = self.get_architecture(cursor,
                  architecture_id)
                req.hdf['downloads.architectures'] = self.get_architectures(req,
                  cursor, order, desc)

            elif mode == 'architectures-post-add':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                architecture = {'name' : req.args.get('name'),
                                'description' : req.args.get('description')}

                # Add architecture.
                self.add_architecture(cursor, architecture)

            elif mode == 'architectures-post-edit':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                architecture_id = req.args.get('id')
                architecture = {'name' : req.args.get('name'),
                                'description' : req.args.get('description')}

                # Add architecture.
                self.edit_architecture(cursor, architecture_id, architecture)

            elif mode == 'architectures-delete':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get selected architectures.
                selection = req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete architectures.
                if selection:
                    for architecture_id in selection:
                        self.delete_architecture(cursor, architecture_id)

            elif mode == 'admin-platforms-list':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                order = req.args.get('order') or 'id'
                desc = req.args.get('desc')
                platform_id = int(req.args.get('platform') or 0)

                # Display platforms.
                req.hdf['downloads.order'] = order
                req.hdf['downloads.desc'] = desc
                req.hdf['downloads.platform'] = self.get_platform(cursor,
                  platform_id)
                req.hdf['downloads.platforms'] = self.get_platforms(req, cursor,
                  order, desc)

            elif mode == 'platforms-post-add':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                platform = {'name' : req.args.get('name'),
                            'description' : req.args.get('description')}

                # Add platform.
                self.add_platform(cursor, platform)

            elif mode == 'platforms-post-edit':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                platform_id = req.args.get('id')
                platform = {'name' : req.args.get('name'),
                            'description' : req.args.get('description')}

                # Add platform.
                self.edit_platform(cursor, platform_id, platform)

            elif mode == 'platforms-delete':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get selected platforms.
                selection = req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete platforms.
                if selection:
                    for platform_id in selection:
                        self.delete_platform(cursor, platform_id)

            elif mode == 'admin-types-list':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values
                order = req.args.get('order') or 'id'
                desc = req.args.get('desc')
                platform_id = int(req.args.get('type') or 0)

                # Display platforms.
                req.hdf['downloads.order'] = order
                req.hdf['downloads.desc'] = desc
                req.hdf['downloads.type'] = self.get_type(cursor, platform_id)
                req.hdf['downloads.types'] = self.get_types(req, cursor, order,
                  desc)

            elif mode == 'types-post-add':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                type = {'name' : req.args.get('name'),
                        'description' : req.args.get('description')}

                # Add type.
                self.add_type(cursor, type)

            elif mode == 'types-post-edit':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get form values.
                type_id = req.args.get('id')
                type = {'name' : req.args.get('name'),
                        'description' : req.args.get('description')}

                # Add platform.
                self.edit_type(cursor, type_id, type)

            elif mode == 'types-delete':
                req.perm.assert_permission('DOWNLOADS_ADMIN')

                # Get selected types.
                selection = req.args.get('selection')
                if isinstance(selection, (str, unicode)):
                    selection = [selection]

                # Delete types.
                if selection:
                    for type_id in selection:
                        self.delete_type(cursor, type_id)

    def _get_file_from_req(self, req):
        file = req.args['file']

        # Test if file is uploaded.
        if not hasattr(file, 'filename') or not file.filename:
            raise TracError('No file uploaded.')
        if hasattr(file.file, 'fileno'):
            size = os.fstat(file.file.fileno())[6]
        else:
            size = file.file.len
        if size == 0:
            raise TracError('Can\'t upload empty file.')

        return file.file, file.filename
