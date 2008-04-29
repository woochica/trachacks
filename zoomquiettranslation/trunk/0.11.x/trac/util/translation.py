# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.

"""Utilities for text translation with gettext."""

from gettext import NullTranslations
import pkg_resources
try:
    import threading
except ImportError:
    import dummy_threading as threading

from babel.support import LazyProxy, Translations

__all__ = ['gettext', 'ngettext', 'gettext_noop', 'ngettext_noop']

_current = threading.local()

def gettext_noop(string, **kwargs):
    retval = string
    if kwargs:
        retval %= kwargs
    return retval
N_ = gettext_noop

def gettext(string, **kwargs):
    def _gettext():
        trans = get_translations().ugettext(string)
        if kwargs:
            trans %= kwargs
        return trans
    if not hasattr(_current, 'translations'):
        return LazyProxy(_gettext)
    return _gettext()
_ = gettext

def ngettext(singular, plural, num, **kwargs):
    def _ngettext():
        trans = get_translations().ungettext(singular, plural, num)
        if kwargs:
            trans %= kwargs
        return trans
    if not hasattr(_current, 'translations'):
        return LazyProxy(_ngettext)
    return _gettext()

def ngettext_noop(singular, plural, num, **kwargs):
    if num == 1:
        retval = singular
    else:
        retval = plural
    if kwargs:
        retval %= kwargs
    return retval

def activate(locale):
    locale_dir = pkg_resources.resource_filename(__name__, '../locale')
    _current.translations = Translations.load(locale_dir, locale)

_null_translations = NullTranslations()

def get_translations():
    return getattr(_current, 'translations', _null_translations)

def deactivate():
    del _current.translations

def get_available_locales():
    """Return a list of locale identifiers of the locales for which
    translations are available.
    """
    return [dirname for dirname
            in pkg_resources.resource_listdir(__name__, '../locale')
            if '.' not in dirname]
