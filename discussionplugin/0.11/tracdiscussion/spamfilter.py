# -*- coding: utf-8 -*-

# Spamfilter imports.
from trac.util import arity
from tracspamfilter.api import RejectContent
try: #SpamFilter < 0.7
    from tracspamfilter.api import FilterSystem
except ImportError: #SpamFilter 0.7+
    from tracspamfilter.filtersystem import FilterSystem

# Local imports.
from tracdiscussion.api import *

class DiscussionSpamFilter(Component):
    """
        The spam filtering component implements adapter for SpamFilterPluging
        which denies to create topics of messages with bad content.
    """
    implements(IDiscussionFilter)

    # IDiscussionFilter methods.

    def filter_topic(self, context, topic):
        # Test topic for spam.
        try:
            if arity(FilterSystem.test) == 4: #SpamFilter < 0.3.2 or >= 0.7.0
                FilterSystem(self.env).test(context.req, topic['author'],
                    [(None, topic['author']), (None, topic['subject']),
                     (None, topic['body'])])
            else: #SpamFilter >= 0.3.2 or < 0.7.0
                FilterSystem(self.env).test(context.req, topic['author'],
                    [(None, topic['author']), (None, topic['subject']),
                     (None, topic['body'])], context.req.remote_addr)
        except RejectContent, error:
            # Topic contains spam.
            return False, error.message

        # Topic is fine.
        return True, topic

    def filter_message(self, context, message):
        # Test message for spam.
        try:
            FilterSystem(self.env).test(context.req, message['author'], [(None,
              message['author']), (None, message['body'])])
        except RejectContent, error:
            # Message contains spam.
            return False, error.message

        # Message is fine.
        return True, message
