# -*- coding: utf8 -*-

import sets

from trac.core import *
from trac.util.html import html

from tractags.api import ITaggingSystemProvider, DefaultTaggingSystem, \
  TagEngine

from tracdownloads.api import *

class DownloadsTaggingSystem(DefaultTaggingSystem):
    """
      Tagging system which returns tags of all created downloads.
    """
    def __init__(self, env):
        DefaultTaggingSystem.__init__(self, env, 'downloads')

    def name_details(self, name):
        # Get cursor.
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Get API object.
        api = self.env[DownloadsApi]

        # Get tagged download.
        download = api.get_download(cursor, name)

        # Return a tuple of (href, wikilink, title)
        defaults = DefaultTaggingSystem.name_details(self, name)
        if download:
            return (defaults[0], html.a(download['file'], href =
              self.env.href.downloads(download['id']), title =
              download['description']), download['description'])
        else:
            return defaults

class DownloadsTags(Component):
    """
        The tags module implements plugin's ability to create tags related
        to downloads.
    """
    implements(ITaggingSystemProvider, IDownloadChangeListener)

    # ITaggingSystemProvider methods.

    def get_tagspaces_provided(self):
        yield 'downloads'

    def get_tagging_system(self, tagspace):
        return DownloadsTaggingSystem(self.env)

    # IDownloadChangeListener methods.

    def download_created(self, download):
        tags = TagEngine(self.env).tagspace.downloads

        # Prepare tag names.
        self._resolve_ids(download)
        tag_names = [download['author'], download['component'],
          download['version'], download['architecture'],
          download['platform'], download['type']]
        if download['tags']:
            tag_names.extend(download['tags'].split(' '))

        # Add tags to download.
        self.log.debug(tag_names)
        tags.replace_tags(None, download['id'], list(sets.Set(tag_names)))

    def download_changed(self, download, old_download):
        tags = TagEngine(self.env).tagspace.downloads

        # Prepare tag names.
        old_download.update(download)
        download = old_download
        self._resolve_ids(download)
        tag_names = [download['author'], download['component'],
          download['version'], download['architecture'],
          download['platform'], download['type']]
        if download['tags']:
            tag_names.extend(download['tags'].split(' '))

        # Add tags to download.
        self.log.debug(tag_names)
        tags.replace_tags(None, download['id'], list(sets.Set(tag_names)))

    def download_deleted(self, download):
        tags = TagEngine(self.env).tagspace.downloads

        # Prepare tag names.
        self._resolve_ids(download)
        tag_names = [download['author'], download['component'],
          download['version'], download['architecture'],
          download['platform'], download['type']]
        if download['tags']:
            tag_names.extend(download['tags'].split(' '))

        # Add tags to download.
        self.log.debug(tag_names)
        tags.remove_tags(None, download['id'], list(sets.Set(tag_names)))

    # Private methods

    def _resolve_ids(self, download):

        # Get database access.
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Resolve architecture platform and type names.
        api = self.env[DownloadsApi]
        architecture = api.get_architecture(cursor, download['architecture'])
        platform = api.get_platform(cursor, download['platform'])
        type = api.get_type(cursor, download['type'])
        self.log.debug(architecture)
        download['architecture'] = architecture['name']
        download['platform'] = platform['name']
        download['type'] = type['name']
