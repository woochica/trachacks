#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2013 Steffen Hoffmann <hoff.st@shaas.net>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Steffen Hoffmann

from trac.core import Component

# Import i18n methods.  Fallback modules maintain compatibility to Trac 0.11
# by keeping Babel optional here.
try:
    from trac.util.translation import domain_functions
    add_domain, _, gettext, tag_ = \
        domain_functions('wikicalendar',
                         ('add_domain', '_', 'gettext', 'tag_'))
except ImportError:
    from genshi.builder import tag as tag_
    from trac.util.translation import gettext
    _ = gettext
    def add_domain(a,b,c=None):
        pass

from wikicalendar.compat import cleandoc
cleandoc_ = cleandoc


__all__ = ['WikiCalendarBuilder']


class WikiCalendarBuilder(Component):
    """Base class for Components providing content for wiki calendar."""

    abstract = True

    def declare(self):
        """Returns an iterable of supported operations.

        Common values are pre-set here.
        """
        return {
            'capability': ['harvest', 'render'],
            'resource': None,
            'target': 'body'
        }

    def harvest(self):
        """
        """
        pass

    def render(self):
        """
        """
        pass
