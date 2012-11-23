# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 Michael Renzmann
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# The Borg class implementation is taken from:
# http://code.activestate.com/recipes/66531/#c20

import re
import threading
from trac.perm import PermissionCache
from trac.wiki.model import WikiPage
from tractags.api import TagSystem

def natural_sort(l):
    """Sort a list of CacheObjects in the way that humans expect."""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key.name)]
    return sorted(l, key=alphanum_key)


class FakeRequest(object):
    def __init__(self, env, authname = 'anonymous'):
        self.perm = PermissionCache(env, authname)


class Borg(object):
    """
    Author: Alex Naanou
    Source: http://code.activestate.com/recipes/66531/#c20
    """
    _state = {}
    _lock = threading.RLock()
    def __new__(cls, *p, **k):
        self = object.__new__(cls, *p, **k)
        self.__dict__ = cls._state
        return self


extract_title = re.compile(r'=\s+([^=]*)=', re.MULTILINE | re.UNICODE)
filter_macros = re.compile(r'\[\[[^\]]*\]\]\s?\n?', re.MULTILINE | re.UNICODE)

class CacheObject(object):
    name = None
    title = None

    def __init__(self, name, env, req, tag_system, get_desc = False, get_tags = False):
        self.name = name
        self._env = env
        self._req = req
        self._tag_system = tag_system
        self._get_description = get_desc
        self._get_tags = get_tags

        self.update()

    def __str__(self):
        return '%s (%s)' % (self.name, self.title)

    def update(self):
        page = WikiPage(self._env, self.name)
        if not page.exists:
            raise RuntimeError('%s: no such wiki page' % self.name)

        match = extract_title.search(page.text)
        if match:
            if match.group(1):
                self.title = match.group(1).strip()
                description = extract_title.sub('', page.text, 1)
            else:
                self.title = None
                description = ''
        else:
            description = page.text

        if self._get_description:
            self.description = filter_macros.sub('', description).strip()
        if self._get_tags:
            self.tags = self._tag_system.get_tags(self._req, page.resource)


class Hack(CacheObject):
    def __init__(self, name, env, req, tag_system):
        CacheObject.__init__(self, name, env, req, tag_system, False, True)


class Tag(CacheObject):
    def __init__(self, name, env, req, tag_system):
        CacheObject.__init__(self, name, env, req, tag_system, True, False)


class HacksCache(Borg):
    _lock = threading.RLock()
    _initialized = False

    _hacks = dict()
    _types = dict()
    _releases = dict()

    def __init__(self, env):
        if self._initialized:
            self._log('already initialized')
            return
        else:
            env.log.debug('HacksCache %x: initializing' % id(self.__dict__))

        self._lock.acquire()

        self._env = env
        self._tag_system = TagSystem(env)
        self._req = FakeRequest(env)
        self.id = id(self.__dict__)

        self._rebuild_cache()

        self._initialized = True
        self._lock.release()
        self._log('initialization finished')

    def __del__(self):
        self._log('Aiiieeeee')

    def _rebuild_cache(self):
        """ Rebuild the cache. Caller MUST hold the lock! """
        self._log('rebuilding cache (initialized=%s)' % self._initialized)
        self._hacks = dict()
        self._types = dict()
        self._releases = dict()

        self._update_types()
        self._update_releases()

        query  = 'realm:wiki (%s) (%s)' % \
            (' or '.join(self._types), ' or '.join(self._releases))
        for h in self._query_tags(query):
            self._update_hack(h, False, False)

    def _log(self, message):
        self._env.log.debug('HacksCache %x: %s' % (self.id, message))

    def _query_tags(self, query):
        """ Helper to perform queries on cached tags system """
        return [ r.id for r, _ in self._tag_system.query(self._req, query) ]

    def _update_types(self):
        """ Get/update list of hack types """
        types = self._query_tags('realm:wiki type')
        keys = self._types.keys()

        # add types that have been added since last update
        for t in types:
            if t not in keys:
                self._types[t] = Tag(t, self._env, self._req, self._tag_system)

        # remove types that no longer exist
        for k in keys:
            if k not in types:
                del self._types[k]

    def _update_releases(self):
        """ Get/update list of Trac releases """
        releases = self._query_tags('realm:wiki release')
        keys = self._releases.keys()

        # add releases that have been added since last update
        for r in releases:
            if r not in keys:
                self._releases[r] = Tag(r, self._env, self._req, self._tag_system)

        # remove releases that no longer exist
        for k in keys:
            if k not in releases:
                del self._releases[k]

    def _update_hack(self, name, full_update = True, check_delete = True):
        """ Get/update/delete hack properties """
        if full_update:
            self._update_types()
            self._update_releases()

        delete = False
        if check_delete:
            page = WikiPage(self._env, name)
            if page.exists:
                tags = set(self._tag_system.get_tags(self._req, page.resource))
                if not (tags.intersection(self._types) and tags.intersection(self._releases)):
                    delete = True
            else:
                delete = True

        if delete:
            try:
                del self._hacks[name]
                self._log('deleted hack %s' % name)
            except:
                self._log('%s is no hack, skipped' % name)
        else:
            try:
                self._hacks[name].update()
                self._log('updated hack %s' % name)
            except:
                self._hacks[name] = Hack(name, self._env, self._req, self._tag_system)
                self._log('learned hack %s' % name)

    def _get(self, where, what):
        try:
            return where[what]
        except:
            return None

    def _get_all(self, where, sorted = False):
        v = where.values()
        if sorted:
            return natural_sort(v)
        else:
            return v


    # Public API
    def update(self, hack = None):
        """ Update cache for all or just the given hack """
        if hack:
            self._update_hack(hack, True, True)
        else:
            self._lock.acquire()
            self._rebuild_cache()
            self._lock.release()

    def get_type(self, name):
        return self._get(self._types, name)

    def get_all_types(self, sorted = False):
        return self._get_all(self._types, sorted)

    def get_release(self, name):
        return self._get(self._releases, name)

    def get_all_releases(self, sorted = False):
        return self._get_all(self._releases, sorted)

    def get_hack(self, name):
        return self._get(self._hacks, name)

    def get_all_hacks(self, sorted = False):
        return self._get_all(self._hacks, sorted)

