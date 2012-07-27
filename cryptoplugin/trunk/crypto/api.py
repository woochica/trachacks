#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from pkg_resources import resource_filename

from trac.core import Component, ExtensionPoint, Interface, implements

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


class IKeyVault(Interface):
    """Defines common key store operations."""

    def keys(self, private=False, id_only=False):
        """Returns the list of all available keys."""

    def has_key(self, key_id, private=False):
        """Returns whether a key with the given ID is available or not."""

    def get_key(self, key_id, private=False):
        """Returns a distinct key as dictionary of key properties."""

    def create_key(self, **kwargs):
        """Generate a new key with specified properties."""

    def delete_key(self, key_id, perm):
        """Delete the key specified by ID."""


class ICipherModule(Interface):
    """Defines common key operations."""


class Credential(Component):

    abstract = True


class GenericFactory(Component):
    """Provides common key store operations."""

    abstract = True
    implements(IKeyVault)
    name = 'generic'

    def keys(self, private=False, id_only=False):
        """Returns the list of all available keys."""
        return []

    def has_key(self, key_id, private=False):
        """Returns whether a key with the given ID is available or not."""
        if key_id in self.keys(private=private, id_only=True):
            return True
        return False

    def get_key(self, key_id, private=False):
        """Returns a distinct key as dictionary of key properties."""
        for key in self.keys(private=private):
            if key_id == key['keyid']:
                return key
        return {}

    def create_key(self, **kwargs):
        """Generate a new key with specified properties."""
        return {}

    def delete_key(self, key_id, perm):
        """Delete the key specified by ID."""
        return False


class CryptoBase(Component):
    """Cryptography foundation for Trac."""

    _key_stores = ExtensionPoint(IKeyVault)

    def __init__(self):
        # Bind 'crypto' catalog to the specified locale directory.
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

    def keys(self, private=False, id_only=False):
        """Returns the list of all available keys."""
        for store in self._key_stores:
            for key in store.keys(private=private, id_only=id_only):
                yield key

    def has_key(self, key_id, private=False):
        """Returns whether a key with the given ID is available or not."""
        if key_id in self.keys(private=private, id_only=True):
            return True
        return False
