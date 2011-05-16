# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Emmanuel Blot <emmanuel.blot@free.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.

from mimetypes import guess_type
from trac.core import *
from trac.attachment import IAttachmentManipulator

__all__ = ['AttachmentFilter']

class AttachmentFilter(Component):
    """Filter out attachments"""
    
    implements(IAttachmentManipulator)

    # IAttachmentManipulator
    
    def prepare_attachment(self, req, attachment, fields):
        pass

    def validate_attachment(self, req, attachment):
        """Validate an attachment after upload but before being stored
        in Trac environment.
        
        Must return a list of ``(field, message)`` tuples, one for
        each problem detected. ``field`` can be any of
        ``description``, ``username``, ``filename``, ``content``, or
        `None` to indicate an overall problem with the
        attachment. Therefore, a return value of ``[]`` means
        everything is OK."""
        (filetype, encoding) = guess_type(attachment.filename)
        self.log.info("Filename %s, filetype %s" % \
            (attachment.filename, filetype))
        if not filetype:
            return []
        filetype = filetype.lower()
        if filetype in self._mime_exclude:
            return [('content', self._mime_exclude[filetype])]
        return []
    
    # Implementation
    
    def __init__(self):
        self._mime_exclude = {}
        self._get_rules(self.config)
        
    def _get_rules(self, config):
        """Usually passed self.config, this will return the parsed ticket-workflow
        section.
        """
        for option, value in config.options('attachment_filter'):
            self._mime_exclude[option.lower()] = value.strip()
