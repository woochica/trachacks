# -*- coding:utf8 -*-
import re, os
from time import time
from glob import glob
from threading import Lock
from tempfile import gettempdir
from trac.core import Component

_lock = Lock()

def with_lock(f):
    def _decorator(*args, **kargs):
        _lock.acquire()
        try:
            return f(*args, **kargs)
        finally:
            _lock.release()
    return _decorator

class Cache(object):
    
    def __init__(self, env):
        self.env = env
        self.use_file_cache = \
                self.env.config.get('blockdiag', 'use_file_cache', '').lower() \
                in ['true', 'yes', 'on', '1']
        if self.use_file_cache:
            self.cachedir = os.path.join(gettempdir(), 'tracblockdiag.cache')
            if not os.path.isdir(self.cachedir):
                try:
                    os.mkdir(self.cachedir)
                    f = open(os.path.join(self.cachedir, 'README'), 'w')
                    f.write('This is cache for TracBlockDiagPlugin. '
                            'These files can be removed safely.')
                    f.close()
                except:
                    if not os.path.isdir(self.cachedir):
                        raise
        
        self._cache = {}
        self.last_compress_at = time()
        
    @with_lock
    def _set_cache(self, id, type, data):
        self._cache[id] = [time(), type, data]
    
    @with_lock
    def _check_cache(self, id):
        if not self._cache.has_key(id):
            return False
        self._cache[id][0] = time()
        return True
        
    @with_lock
    def _get_from_memory_cache(self, id):
        if self._cache.has_key(id):
            val = self._cache[id]
            val[0] = time()
            return val[2]
        else:
            return None
        
    def cache(self, id, type, func):
        
        self.compress()
        
        if self.use_file_cache:
            # NOTE : We check existance of file cache directly, not memory cache.
            # Because sometimes memory cache is accidentally remained after file
            # cache is dropped, and it can makes problem in other process.
            cache_path = os.path.join(self.cachedir, id + "." + type)
            if os.path.isfile(cache_path):
                try:
                    # touch file
                    os.utime(cache_path, None)
                    return
                except Exception, e:
                    self.env.log.debug('(blockdiag) Failed to touch (%s, %s, %r)' % (id ,type, e))
                    if os.path.isfile(cache_path):
                        return
        else:
            if self._check_cache(id):
                return
        
        # create and cache data
        data = func()
        self._set_cache(id, type, data)
        
        if self.use_file_cache:
            try:
                f = open(cache_path, 'wb')
                try:
                    f.write(data)
                finally:
                    f.close()
            except:
                if not os.path.exists(cache_path):
                    raise
        
    def get(self, id, type):
        self.env.log.debug('(blockdiag) get data from cache by %s, %s' % (id ,type))
        data = self._get_from_memory_cache(id)
        if data:
            self.env.log.debug('(blockdiag) data is found in memory cache (%s, %s)' % (id ,type))
            return data
        
        if self.use_file_cache:
            cache_path = os.path.join(self.cachedir, id + "." + type)
            if os.path.isfile(cache_path):
                self.env.log.debug('(blockdiag) data is found in file cache (%s, %s)' % (id ,type))
                f = open(cache_path, 'rb')
                try:
                    data = f.read()
                finally:
                    f.close()
                self._set_cache(id, type, data)
                return data
            else:
                return None
        else:
            return None
    
    def compress(self):
        now = time()
        if now < self.last_compress_at + 600:
            return
        self.last_compress_at = now
        
        self.env.log.debug('(blockdiag) Compress memory cache')
        
        @with_lock
        def compress_memory_cache():
            for (key, value) in self._cache.items():
                if value[0] < now - 600:
                    del(self._cache[key])
        compress_memory_cache()
        
    
