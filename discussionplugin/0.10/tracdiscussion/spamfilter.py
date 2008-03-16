# -*- coding: utf-8 -*-
# Spam adapter for tracdiscussion
# Written by: Michael Medin <michael [at] medin [dot] name>
#

from trac.core import *
from trac.util.text import to_unicode

from tracspamfilter.api import FilterSystem

from tracdiscussion.api import IDiscussionManipulator

class DiscussionSpamFilter(Component):
    """
        Module implementing spam filter.
    """
    implements(IDiscussionManipulator)

    # IDiscussionManipulator methods.

    def validate_message(self ,req, author, body):
        if req.perm.has_permission('TICKET_ADMIN'):
            # An administrator is allowed to spam
            return []
        if 'preview' in req.args:
            # Only a preview, no need to filter the submission yet
            return []
        changes = [(None, body)]
        FilterSystem(self.env).test(req, author, changes)
        return []

    def validate_topic(self, req, author, subject, body):
        if req.perm.has_permission('TICKET_ADMIN'):
            # An administrator is allowed to spam
            return []
        if 'preview' in req.args:
            # Only a preview, no need to filter the submission yet
            return []
        changes = [(None, body)]
        FilterSystem(self.env).test(req, author, changes)
        return []

