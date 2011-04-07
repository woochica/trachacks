# -*- coding: utf8 -*-

import os
import os.path

from trac.core import *
from trac.admin import AdminCommandError
from trac.perm import PermissionCache
from trac.mimeview import Context
from trac.util.translation import _
from trac.util.text import to_unicode, print_table, pretty_size

from trac.admin import IAdminCommandProvider

from tracdownloads.api import *

class FakeRequest(object):
    def __init__(self, env, authname):
        self.perm = PermissionCache(env, authname)

class DownloadsConsoleAdmin(Component):
    """
        The consoleadmin module implements downloads plugin administration
        via trac-admin command.
    """
    implements(IAdminCommandProvider)

    # Download change listeners.
    change_listeners = ExtensionPoint(IDownloadChangeListener)

    # Configuration options.
    path = Option('downloads', 'path', '/var/lib/trac/downloads',
      doc = 'Directory to store uploaded downloads.')
    consoleadmin_user = Option('downloads', 'consoleadmin_user', 'anonymous',
      doc = 'User whos permissons will be used to upload download. He/she'
        ' should have TAGS_MODIFY permissons.')

    # IAdminCommandProvider

    def get_admin_commands(self):
        yield ('download list', '', 'Show uploaded downloads', None,
          self._do_list)
        yield ('download add', '<file> [description=<description>]'
          ' [author=<author>]\n  [tags="<tag1> <tag2> ..."]'
          ' [component=<component>] [version=<version>]\n'
          '  [architecture=<architecture>] [platform=<platform>]'
          ' [type=<type>]', 'Add new download', None,
          self._do_add)
        yield ('download remove', '<filename> | <download_id>',
          'Remove uploaded download', None, self._do_remove)

    # Internal methods.

    def _do_list(self):
        # Get downloads API component.
        api = self.env[DownloadsApi]

        # Create context.
        context = Context('downloads-consoleadmin')
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()

        # Print uploded download
        downloads = api.get_downloads(context)
        print_table([(download['id'], download['file'], pretty_size(
          download['size']), format_datetime(download['time']),
          download['component'],  download['version'],
          download['architecture']['name'], download['platform']['name'],
          download['type']['name']) for download in downloads], ['ID',
          'Filename', 'Size', 'Uploaded', 'Component', 'Version',
          'Architecture', 'Platform', 'Type'])

    def _do_add(self, filename, *arguments):
        # Get downloads API component.
        api = self.env[DownloadsApi]

        # Create context.
        context = Context('downloads-consoleadmin')
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()
        context.req = FakeRequest(self.env, self.consoleadmin_user)

        # Convert relative path to absolute.
        if not os.path.isabs(filename):
            filename = os.path.join(self.path, filename)

        # Open file object.
        file, filename, file_size = self._get_file(filename)

        # Create download dictionary from arbitrary attributes.
        download = {'file' : filename,
                    'size' : file_size,
                    'time' : to_timestamp(datetime.now(utc)),
                    'count' : 0}

        # Read optional attributes from arguments.
        for argument in arguments:
            # Check correct format.
            argument = argument.split("=")
            if len(argument) != 2:
                AdminCommandError(_('Invalid format of download attribute:'
                  ' %(value)s', value = argument))
            name, value = argument

            # Check known arguments.
            if not name in ('description', 'author', 'tags', 'component', 'version',
              'architecture', 'platform', 'type'):
                raise AdminCommandError(_('Invalid download attribute:' 
                  ' %(value)s', value = name))

            # Transform architecture, platform and type name to ID.
            if name == 'architecture':
                value = api.get_architecture_by_name(context, value)['id']
            elif name == 'platform':
                value = api.get_platform_by_name(context, value)['id']
            elif name == 'type':
                value = api.get_type_by_name(context, value)['id']

            # Add attribute to download.
            download[name] = value

        self.log.debug(download)

        # Upload file to DB and file storage.
        api.store_download(context, download, file)

        # Close input file and commit changes in DB.
        file.close()
        db.commit()

    def _do_remove(self, identifier):
        # Get downloads API component.
        api = self.env[DownloadsApi]

        # Create context.
        context = Context('downloads-consoleadmin')
        db = self.env.get_db_cnx()
        context.cursor = db.cursor()
        context.req = FakeRequest(self.env, self.consoleadmin_user)

        # Get download by ID or filename.
        try:
            download_id = int(identifier)
            download = api.get_download(context, download_id)
        except ValueError:
            download = api.get_download_by_file(context, identifier)

        # Check if download exists.
        if not download:
            raise AdminCommandError(_('Invalid download identifier: %(value)s',
              value = identifier))

        # Delete download by ID.
        api.delete_download(context, download_id)

        # Commit changes in DB.
        db.commit()

    def _get_file(self, filename):
        # Open file and get its size
        file = open(filename, 'rb')
        size = os.fstat(file.fileno())[6]

        # Check non-emtpy file.
        if size == 0:
            raise TracError('Can\'t upload empty file.')

        # Try to normalize the filename to unicode NFC if we can.
        # Files uploaded from OS X might be in NFD.
        filename = unicodedata.normalize('NFC', to_unicode(filename, 'utf-8'))
        filename = filename.replace('\\', '/').replace(':', '/')
        filename = os.path.basename(filename)

        return file, filename, size
