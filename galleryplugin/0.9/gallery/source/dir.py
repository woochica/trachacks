# -*- coding: iso8859-1 -*-
#
# Copyright (C) 2003-2005 Edgewall Software
# Copyright (C) 2005 Bruce Christensen <trac@brucec.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# Author: Bruce Christensen <trac@brucec.net>

import os
from PIL import Image
from glob import glob

from trac.core import *
from gallery.api import *

class DirectoryGallerySource(Component):
    """
    Provide gallery images from a filesystem directory.
    """
    
    implements(IGallerySource)

    default_extensions = 'jpeg, JPEG, jpg, JPG, gif, GIF, png, PNG'

    def __init__(self):
        self.env.log.debug("Initializing DirectoryGallerySource")

    # IGallerySource methods

    def gallery_source_name(self):
        return 'dir'

    def get_tags(self):
        # db = self.env.get_db_cnx()
        # cursor = db.cursor()
        # cursor.execute("SELECT DISTINCT tag FROM gallery_tag WHERE source=%s",
        #                (self.gallery_source_name(),))
        # while 1:
        #     row = cursor.fetchone()
        #     if not row:
        #         break
        #     yield row[0]
        # cursor.close()
        return ['tag'] # FIXME

    def get_images(self, gallery, tag=None):
        self.env.log.debug("Gallery still: '%s'" % gallery)
        cfg = self.env.config
        extensions = cfg.get('gallery', 'extensions', self.default_extensions)
        extensions = [ext.strip() for ext in extensions.split(',')]
        dirs = [d.strip() for d in cfg.get('gallery', 'directories').split(',')]

        self.env.log.debug(dirs)

        for dir in dirs:
            for ext in extensions:
                pattern = os.path.join(dir, '*' + os.path.extsep + ext)
                self.env.log.debug("Pattern: '%s'" % pattern)
                for path in glob(pattern):
                    self.env.log.debug("Path: '%s'" % path)
                    self.env.log.debug("Gallery still: '%s'" % gallery)
                    img = self.get_image(gallery, path)
                    if not tag or tag in img.tags:
                        self.env.log.debug("Okay")
                        yield img
                    else:
                        self.env.log.debug("Bad")

    def get_image(self, gallery, path):
        return DirectoryGalleryImage(self, path, gallery)


class DirectoryGalleryImage(GalleryImage):
    """
    Gallery image that comes from a directory on the filesystem.
    """

    # GalleryImage methods

    def __init__(self, source, path, gallery):
        GalleryImage.__init__(self, source, path, gallery)

        self._img = None
        self.thumb = GalleryThumbnail(self)

    def fetch(self):
        if not self._img:
            self._img = Image.open(self.path)
        
        stat_result = os.stat(self.path)

        self.width, self.height = self._img.size
        self.mimetype = Image.MIME[self._img.format]
        self.size = stat_result.st_size
        self.time = stat_result.st_mtime

        self.title = 'No title'
        self.description = 'No description'
        self.author = 'anonymous'
        self.ipnr = 'none'
        self.thumb = GalleryThumbnail(self)
        self.tags = ['tag'] # FIXME


    def can_store(self):
        return False

    def can_delete(self):
        return False

    def open(self):
        return open(self.path, 'r')
