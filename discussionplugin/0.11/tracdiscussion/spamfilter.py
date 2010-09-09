# -*- coding: utf-8 -*-

# Spamfilter imports.
from tracspamfilter.api import FilterSystem, RejectContent

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
            FilterSystem(self.env).test(context.req, topic['author'], [(None,
              topic['author']), (None, topic['subject']), (None,
              topic['body'])])
        except RejectContent, error:
            # Topic contains spam.
            return (False, error.message)

        # Topic is fine.
        return (True, topic)

    def filter_message(self, context, message):
        # Test message for spam.
        try:
            FilterSystem(self.env).test(context.req, message['author'], [(None,
              message['author']), (None, message['body'])])
        except RejectContent, error:
            # Message contains spam.
            return (False, error.message)

        # Message is fine.
        return (True, message)
