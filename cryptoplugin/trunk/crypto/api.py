#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from pkg_resources import resource_filename

from trac.core import Component

# Import standard i18n methods.
try:
    from trac.util.translation import domain_functions
    add_domain, _, gettext, ngettext, tag_ = \
        domain_functions('crypto', ('add_domain', '_', 'gettext',
                                      'ngettext', 'tag_'))
    dgettext = None
except ImportError:
    # Fallback modules maintain compatibility to Trac 0.11 by keeping Babel
    # optional here.
    from genshi.builder import tag as tag_
    from trac.util.translation import gettext
    _ = gettext
    def add_domain(a,b,c=None):
        pass
    def dgettext(domain, string, **kwargs):
        return safefmt(string, kwargs)
    def ngettext(singular, plural, num, **kwargs):
        string = num == 1 and singular or plural
        kwargs.setdefault('num', num)
        return safefmt(string, kwargs)
    def safefmt(string, kwargs):
        if kwargs:
            try:
                return string % kwargs
            except KeyError:
                pass
        return string


class CryptoBase(Component):
    """Cryptography foundation for Trac."""

    def __init__(self):
        # Bind 'crypto' catalog to the specified locale directory.
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)
