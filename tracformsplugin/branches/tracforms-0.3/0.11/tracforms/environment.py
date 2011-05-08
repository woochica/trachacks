# -*- coding: utf-8 -*-

import fnmatch
import re

from api import _
from compat import json


class FormEnvironment(dict):
    """Handles the environment used by TracForms macros.

This dictionary is stackable and provides recursive context
for pseudo-variables.

>>> outer = FormEnvironment(None)
>>> outer['hello'] = 'World'
>>> outer['test:ACK'] = 'OOP'
>>> outer['test:FOO'] = 'BAR'
>>> inner = FormEnvironment(outer, ('test:',))
>>> inner['hello']
'World'
>>> inner['ACK']
'OOP'
>>> inner.getmany('test:*')
('OOP', 'BAR')
>>> tuple(sorted(inner.keyset('/.el/')))
('hello',)
>>> tuple(sorted(inner.keyset('/.el/')))
('hello',)
>>> tuple(sorted(inner.keyset('*')))
('test:ACK', 'test:FOO')
>>> tuple(sorted(inner.keyset('*', all=True)))
('hello', 'test:ACK', 'test:FOO')
>>> inner.getmany('/.el/')
('World',)
>>> web = FormEnvironment(None, ('test',))
>>> web.addform('a=5&a=7&b=hello', 'test')
>>> web['a']
'5\t7'
    """

    def __init__(self, base=None, prefixes=()):
        if base is not None:
            self.update(base)
        self.base = base
        self.prefixes = prefixes + ('',)

    def __getitem__(self, key, NOT_FOUND=KeyError):
        obj = self.get(key, NOT_FOUND)
        if obj is NOT_FOUND:
            raise KeyError(key)
        else:
            return obj

    def get(self, search, default=None, singleton=True, all=False):
        values = tuple(dict.__getitem__(self, key)
                        for key in sorted(self.keyset(search, all)))
        if singleton:
            if not values:
                return default
            elif len(values) == 1:
                return values[0]
            else:
                raise ValueError(
                    _("Too many results for singleton %r" % key))
        else:
            return values

    def keyset(self, search, all=False):
        if search[:1] == '/' and search[-1:] == '/':
            def matches(prefix, keys):
                regexp = re.compile(prefix + search[1:-1])
                return (key for key in keys
                        if regexp.match(key))
        elif '*' in search or '?' in search or '|' in search:
            def matches(prefix, keys):
                regexp = re.compile(fnmatch.translate(prefix + search))
                return (key for key in keys
                        if regexp.match(key))
        else:
            def matches(prefix, keys):
                check = prefix + search
                return (key for key in keys
                        if key == check)
        keys = self.sorted_keys
        values = set()
        for prefix in self.prefixes:
            values |= set(key for key in matches(prefix, keys))
            if values and not all:
                break
        return values

    _sorted = None
    @property
    def sorted_keys(self):
        keys = self._sorted
        if keys is None:
            keys = self._sorted = sorted(self)
        return keys

    def getmany(self, search, all=False):
        return self.get(search, singleton=False, all=all)

    def addform(self, data):
        for name, value in json.loads(state or '{}').iteritems():
            keys = [prefix + ':' + name for prefix in self.prefixes]
            for key in keys:
                self[key] = tuple(value)

