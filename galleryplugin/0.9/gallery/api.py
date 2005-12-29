# -*- coding: iso8859-1 -*-
#
# Copyright (C) 2003-2005 Edgewall Software
# Copyright (C) 2003-2005 Jonas Borgström <jonas@edgewall.com>
# Copyright (C) 2005 Christopher Lenz <cmlenz@gmx.de>
# Copyright (C) 2005 Bruce Christensen <trac@brucec.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# Author: Bruce Christensen <trac@brucec.net>
#         Jonas Borgström <jonas@edgewall.com>
#         Christopher Lenz <cmlenz@gmx.de>

import urllib
import md5
import os
import Image, ImageFile

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.util import create_unique_file
from trac.db import Table, Column, Index, DatabaseManager

__all__ = ['IGallerySource', 'Gallery', 'GalleryImage', 'GalleryThumbnail']


class IGallerySource(Component):
    """
    Source of images for the gallery.
    """

    def gallery_source_name():
        """
        @return: a unique short string identifier for this gallery source, e.g.
          'tracenv', 'svn', or 'filesystem'. This can be used to identify the
          source in the database.
        """

    def get_tags():
        """
        @return: an iterable of all tag strings used by images in this source
        """

    def get_images(gallery, tag=None):
        """
        @return: an iterable of GalleryImage objects available from this source
        @param gallery: the Gallery object requesting the images
        @param tag: if specified, return only images with the specified tag
        """

    def get_image(gallery, path):
        """
        @return: the GalleryImage object corresponding to the specified path
        @param gallery: the Gallery object requesting the images
        @param path: the unique string path of the image that is to be returned
        @raise KeyError: if there is no image located at the specified path
        """


class Gallery(Component):
    """A collection of images with metadata and thumbnails."""

    implements(IEnvironmentSetupParticipant)

    _sources = ExtensionPoint(IGallerySource)

    # Directories inside the environment where gallery data is stored
    GALLERY_DIR = 'gallery'
    THUMB_DIR = 'gallery/thumbs'

    DB_VERSION = 1
    SCHEMA = [
        Table('gallery_thumb', key=('source', 'path'))[
            Column('source'),
            Column('path'),
            Column('filename'),
            Column('width', type='int'),
            Column('height', type='int'),
            Column('mimetype'),
            Column('time', type='int')],
        Table('gallery_tag', key=('source', 'path'))[
            Column('source'),
            Column('path'),
            Column('tag')],
        ]

    def __init__(self):
        self.env.log.debug("Initializing Gallery component")

        self.path = os.path.normpath(
            os.path.join(self.env.path, self.GALLERY_DIR))
        self.thumb_path = os.path.normpath(
            os.path.join(self.env.path, self.THUMB_DIR))

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self._create_directories()
        self._upgrade_db()

    def environment_needs_upgrade(self, db):
        upgrade = {'components': []}

        for path in self.path, self.thumb_path:
            if not os.path.isdir(path):
                upgrade['components'].append('directories')
                break

        cursor = db.cursor()
        cursor.execute("SELECT value FROM system "
                       "WHERE name='gallery_db_version'")
        if cursor.rowcount != 1:
            upgrade['components'].append('db')
            upgrade['old_db_version'] = 0
        else:
            db_version = int(cursor.fetchone()[0])
            if db_version < self.DB_VERSION:
                upgrade['components'].append('db')
                upgrade['old_db_version'] = db_version
        cursor.close()

        self.env.log.debug("Environment upgrade: %s" % upgrade)

        if upgrade['components']:
            self._env_upgrade = upgrade
        return bool(upgrade['components'])

    def upgrade_environment(self, db):
        if 'db' in self._env_upgrade['components']:
            self._upgrade_db(db, self._env_upgrade['old_db_version'])
        if 'directories' in self._env_upgrade['components']:
            self._create_directories()
        del self._env_upgrade

    # Environment creation helper methods

    def _create_directories(self):
        """
        Create the gallery and thumbnail directories.
        """
        for path in self.path, self.thumb_path:
            if not os.path.isdir(path):
                self.env.log.debug("About to create path: '%s'" % path)
                os.makedirs(path)

    def _upgrade_db(self, db, old_version=0):
        """
        Upgrade the db to the latest version.

        @param old_version: the version to upgrade from
        """

        db_backend, _ = DatabaseManager(self.env)._get_connector()
        cursor = db.cursor()
        for table in self.SCHEMA:
            for stmt in db_backend.to_sql(table):
                cursor.execute(stmt)
            self.env.log.debug("Done creating table %s" % table)

        cursor.execute("DELETE FROM system WHERE name='gallery_db_version'")
        cursor.execute("INSERT INTO system (name, value) "
                       "VALUES ('gallery_db_version', %s)", (self.DB_VERSION,))

        self.env.log.debug("Done creating tables.")

    # Public API

    def get_images(self, tag=None):
        """
        Generate a sequence of all known images.

        @param tag: if specified, return only images with the specified tag
        @return: an iterable of GalleryImage objects.
        """
        for source in self._sources:
            for image in source.get_images(tag=tag):
                yield image
    images = property(get_images)

    def _get_tags(self):
        """
        Generate a sequence of all known image tags, in alphabetical order.
        @return: an iterable of all known tag strings.
        """
        tags = {}

        for source in self._sources:
            for tag in source.get_tags():
                tags[tag] = True

        tags = tags.keys().sort()
        return tags
    tags = property(_get_tags)


class GalleryImage(object):
    """
    Base class for an image that is to be displayed in an image gallery.

    Can be overridden to create subclasses for images from different sources.
    One use of this would be to store metadata as svn properties instead of as
    db fields.
    """

    def __init__(self, source, path, gallery):
        """
        Initialize a new gallery image object.

        @param source:  IGallerySource object where this image is stored
        @param path:    string path of this image within the gallery source
        @param gallery: Gallery object this image belongs to
        """

        # self.env.log.debug("Initializing GalleryImage object for '%s:%s'" %
        #                    (source.gallery_source_name(), path))

        # Storage location
        self.source = source
        self.path = path
        self.gallery = gallery
                            
        # Image data
        self.width = None       # integer width of this image, in pixels
        self.height = None      # integer height of this image, in pixels
        self.size = None        # integer size of the image data, in bytes
        self.mimetype = None    # string image MIME type
        self.time = None        # UNIX timestamp when image was last modified

        # Gallery data
        self.title = None       # short image title
        self.description = None # longer image description
        self.author = None      # person who added image
        self.ipnr = None        # IP of person who added image
        self.thumb = None       # this image's GalleryThumbnail object
        self.tags = []          # list of this image's tags

    def fetch(self):
        """
        Fetch image metadata.
        """
        raise NotImplementedError

    def can_store(self):
        """
        @return: True if this image's metadata can be modified
        """
        raise NotImplementedError

    def store(self):
        """
        Save image metadata.
        """
        raise NotImplementedError

    def can_delete(self):
        """
        @return: True if this image can be deleted
        """
        raise NotImplementedError

    def delete():
        """
        Delete this image and its metadata. Also delete its thumbnail.

        @raise: TracError if the image cannot be deleted.
        """
        raise NotImplementedError

    def open(self):
        """
        @return: stream object of image data. Stream object has these methods:
          read([x]): return x bytes from the data stream as a string. When EOF
            is reached, return empty string.
          close(): (optional) close the data stream
        """
        raise NotImplementedError

    def __str__(self):
        self.fetch()
        return "%s: %s" % (self.source.gallery_source_name(), self.path)


class GalleryThumbnail(object):
    """
    A scaled-down representation of a gallery image.
    """

    # Allowed PIL formats that can be used to save thumbnails, with MIME types
    ALLOWED_FORMATS = {
        'PNG': 'image/png',
        'GIF': 'image/gif',
        'JPEG': 'image/jpeg',
        }

    # File type to use if an image is not one of the allowed formats
    DEFAULT_FORMAT = 'PNG'

    def __init__(self, img, db=None):
        """
        @param img: the GalleryImage object that this thumbnail represents
        @param db: open database connection
        """
        self._img = img
        self._db = db
        self._handle_ta = False # Do we handle commits/rollbacks?
        if not db:
            self._db = img.gallery.env.get_db_cnx()
            self._handle_ta = True

        # Call fetch() to retrieve these
        self.filename = None    # string path of the image, inside
                                # [trac_env_dir]/gallery/thumbs
        self.width = None       # thumbnail image width, in pixels
        self.height = None      # thumbnail image height, in pixels
        self.mimetype = None    # thumbnail image MIME type
        self.time = None        # UNIX timestamp when the image this thumbnail
                                # represents was last modified (not necessarily
                                # the time that the thumbnail was generated)

        # Has this thumbnail's data been fetched?
        self._is_fetched = False

    def fetch(self):
        """
        Retrieve thumbnail metadata from the db if it hasn't already been
        retrieved.

        @raise TracError: if no data for self._img is found
        """
        if self._is_fetched:
            return

        source_name = self._img.source.gallery_source_name()
        img_path = self._img.path

        cursor = self._db.cursor()
        cursor.execute("SELECT filename, width, height, mimetype, time "
                       "FROM gallery_thumb WHERE source=%s AND path=%s "
                       "ORDER BY time", (source_name, img_path))
        row = cursor.fetchone()
        cursor.close()

        if not row:
            raise TracError(
                "Image '%s' from '%s' does not exist." %(img_path, source_name),
                'Invalid Image')

        self.filename, self.width, self.height, self.mimetype, self.time = row
        self._is_fetched = True

    def generate(self, maxwidth, maxheight, force=False):
        """
        Generate a new thumbnail image file if any of these are true:
          1. force is true.
          2. There is currently no thumbnail metadata.
          3. The thumbnail's timestamp differs from the source image's.
          4. There is currently no thumbnail image file.

        Otherwise, return without doing anything.

        @param maxwidth: integer max width of thumbnail
        @param maxheight: integer max height of thumbnail
        @param force: if true, then a new thumbnail will be generated
          unconditionally. This can be used to regenerate all thumbnails, such
          as when the user changes the size thumbnail size preference.
        """

        # Decide if this method needs to run
        if not force:
            has_no_metadata = False
            try:
                self.fetch()
            except TracError:
                has_no_metadata = True

            if not (has_no_metadata
                    or self.time != self._img.time
                    or not os.path.exists(self.path)):
                return

        self._img.gallery.env.log.debug("Generating thumbnail for %s" % self._img.path)
        # Create thumbnail and save to file
        thumb = self._create_thumb(maxwidth, maxheight)
        filename, file = self._create_file()
        format = thumb.format
        format = format in self.ALLOWED_FORMATS \
            and format or self.DEFAULT_FORMAT
        thumb.save(file, format)
        file.close()

        # Calculate metadata
        commonprefix = os.path.commonprefix(
            (self._img.gallery.thumb_path, filename))
        self.filename = filename[len(commonprefix) + len(os.path.sep):]
        self.width, self.height = thumb.size
        self.mimetype = self.ALLOWED_FORMATS[format]
        self.time = self._img.time

        # Save metadata to db
        self._store()

    def delete(self):
        """
        Delete this thumbnail's file and metadata.
        """
        self.fetch()

        os.remove(self.path)

        cursor = self._db.cursor()
        cursor.execute("DELETE FROM gallery_thumb WHERE source=%s AND path=%s",
                       (self._img.source.gallery_source_name(), self._img.path))
        cursor.close()
        if self._handle_ta:
            db.commit()

    def _store(self):
        """
        Save thumbnail metadata to DB. Replaces any info already in the db.
        """

        source_name = self._img.source.gallery_source_name()

        self._img.fetch()

        self._img.gallery.env.log.debug(
           (source_name, self._img.path, self.filename,
           self.width, self.height, self.mimetype, self.time))

        cursor = self._db.cursor()
        cursor.execute("DELETE FROM gallery_thumb "
                       "WHERE source=%s AND path=%s",
                       (source_name, self._img.path))
        cursor.execute("INSERT INTO gallery_thumb "
                       "(source, path, filename, width, height, mimetype, time)"
                       " VALUES (%s, %s, %s, %d, %d, %s, %d)",
                       (source_name, self._img.path, self.filename,
                       self.width, self.height, self.mimetype, self.time))
        cursor.close()

        if self._handle_ta:
            self._db.commit()

    def _img_from_stream(self, stream):
        """
        Read data from a byte stream and return an Image object.

        @raise: TracError if an image can't be parsed from the stream
        """

        # Bytes of image data to read at once
        READ_BUF_LEN = 1024

        parser = ImageFile.Parser()
        while 1:
            data = stream.read(READ_BUF_LEN)
            if not data:
                break
            parser.feed(data)

        img = parser.close()

        if img is None:
            raise TracError("Couldn't read image from stream")

        return img

    def _create_thumb(self, maxwidth, maxheight):
        """
        Create an in-memory thumbnail of the parent image.

        @param maxwidth: integer max width of thumbnail
        @param maxheight: integer max height of thumbnail
        @return: Image object that contains thumbnail.
        @raise: TracError if the parent image couldn't be read
        """

        # Read parent image data into Image object
        stream = self._img.open()
        try:
            thumb = self._img_from_stream(stream)
        except TracError:
            raise TracError("Couldn't read image '%s' from source '%s'" % (
                self._img.path, source_name))

        try:
            stream.close()
        except AttributeError:
            # stream isn't required to have a close() method
            pass

        thumb.thumbnail((maxwidth, maxheight), Image.ANTIALIAS)

        return thumb

    def _create_file(self):
        """
        Create a file with a unique name in the thumbnail directory and opens it
        for writing. Doesn't actually write any data to the file.

        @raise: TracError if a file couldn't be created
        @return: 2-tuple: (filename, open writable file descriptor)
        """
        filename = os.path.join(
            self._img.gallery.thumb_path,
            urllib.quote(os.path.split(self._img.path)[1])
            )
        try:
            return create_unique_file(filename)
        except Exception:
            # Couldn't come up with a unique filename, so try adding an MD5 hash
            # to make name unique
            to_hash = self._img.source.gallery_source_name() + '|' + filename
            parts = os.path.splitext(filename)
            hash_hex = md5.new(to_hash).hexdigest()
            filename = "%s.%s.%s" % (parts[0], hash_hex, parts[1])
            #try:
            if 1:
                return create_unique_file(filename)
            #except Exception:
                #raise TracError("Couldn't create unique filename for thumbnail "
                                #"of image '%s' from source '%s'" %
                                #(self._img.path,
                                #self._img.source.gallery_source_name()))

    def _get_path(self):
        """
        @return: the absolute filesystem path to the thumbnail image file
        """
        self.fetch()
        path = os.path.join(self._img.gallery.thumb_path, self.filename)
        return os.path.normpath(path)
    path = property(_get_path)
