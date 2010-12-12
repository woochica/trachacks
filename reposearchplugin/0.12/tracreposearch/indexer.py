"""

Indexing engine for Trac's repository. Implemented using the algorithm
described at:

    http://mail.zope.org/pipermail/zope/2000-April/107218.html

"""

from trac.core import TracError
from tracreposearch.search import TracRepoSearchPlugin
from tracreposearch.lock import lock, unlock, LOCK_EX
from trac.versioncontrol.api import Node
from trac.mimeview.api import Mimeview
import time
import anydbm
import re
from os.path import pathsep
import os

try:
    set()
except:
    from sets import Set as set

class psetdict(object):
    """ Wrapper around anydbm to persistently store a dictionary of sets. """

    def __init__(self, file, mode):
        self._cache = {}
        self._flush = {}
        self.dbm = anydbm.open(file, mode)

    def __contains__(self, key):
        key = key.encode('utf-8')
        return key in self._cache or key in self.dbm

    def __getitem__(self, key):
        key = key.encode('utf-8')
        if key in self._cache:
            return self._cache[key]
        return self._cache.setdefault(key, set(self.dbm[key].decode('utf-8').split(pathsep)))

    def __setitem__(self, key, value):
        key = key.encode('utf-8')
        self._cache[key] = self._flush[key] = value

    def __delitem__(self, key):
        found = 0
        key = key.encode('utf-8')
        if key in self._cache:
            del self._cache[key]
            found += 1
        if key in self._flush:
            del self._flush[key]
            found += 1
        if key in self.dbm:
            del self.dbm[key]
            found += 1
        if not found:
            raise KeyError(key)

    def keys(self):
        return [k.decode('utf-8') for k in self.dbm.keys()]

    def sync(self):
        for key, value in self._flush.iteritems():
            self.dbm[key] = pathsep.join(value).encode('utf-8')
        self.dbm.sync()

    def __del__(self):
        self.sync()

index_lock = None
lock_count = 0

def acquire_lock():
    # This is not ideal...
    global index_lock, lock_count
    lock_count += 1
    if lock_count == 1:
        index_lock = open('/tmp/repo-search.lock', 'w+')
        lock(index_lock, LOCK_EX)

def release_lock():
    global index_lock, lock_count
    lock_count -= 1
    if lock_count == 0:
        index_lock.close()
        index_lock = None

def synchronized(f):
    """ Synchronization decorator. """
    def wrap(*args, **kw):
        acquire_lock()
        try:
            return f(*args, **kw)
        finally:
            release_lock()
    return wrap

class Indexer:
    _strip = re.compile(r'\S+',re.U)

    def __init__(self, env):
        self.env = env
        self.repo = self.env.get_repository()

        if not self.env.config.get('repo-search', 'index',
                                   os.getenv('PYTHON_EGG_CACHE', None)):
            raise TracError("Repository search plugin indexer is not " \
                            "configured correctly. Set the 'index' option " \
                            "under the 'repo-search' section to the full " \
                            "(writable) path to the index.")

        # TODO Should this use the repo location as well?
        env_id = '%08x' % abs(hash(self.env.path))
        self.index_dir = self.env.config.get('repo-search', 'index',
                         os.path.join(os.getenv('PYTHON_EGG_CACHE', ''),
                                      env_id + '.reposearch.idx'))
        self.env.log.debug('Repository search index: %s' % self.index_dir)
        self.minimum_word_length = int(self.env.config.get('repo-search',
                                       'minimum-word-length', 3))

        if not os.path.isdir(self.index_dir):
            os.makedirs(self.index_dir)
            open(os.path.join(self.index_dir, 'README.txt'), 'w').write(
                "This is the Trac RepoSearch plugin's index, for the "
                "Trac environment located at %s\n" % self.env.path)

        try:
            self._open_storage('r')
        except:
            self.reindex()

    def _open_storage(self, mode):
        # Stores meta information; last repo version, include list, etc.
        self.meta = anydbm.open(os.path.join(self.index_dir, 'meta.db'), mode)
        # word:file mapping
        self.words = psetdict(os.path.join(self.index_dir, 'words.db'), mode)
        # bigram:word mapping
        self.bigrams = psetdict(os.path.join(self.index_dir, 'bigrams.db'), mode)
        # file:rev mapping
        self.revs = anydbm.open(os.path.join(self.index_dir, 'revs.db'), mode)
        # file:words mapping
        self.files = psetdict(os.path.join(self.index_dir, 'files.db'), mode)
        # Probably need a word:bigram mapping table as well :\
    _open_storage = synchronized(_open_storage)

    def _bigram_word(self, word):
        for start in range(0, len(word) - 1):
            yield word[start:start + 2]

    def sync(self):
        self.meta['last-repo-rev'] = unicode(self.repo.youngest_rev)
        self.meta['index-include'] = self.env.config.get('repo-search', 'include', '')
        self.meta['index-exclude'] = self.env.config.get('repo-search', 'exclude', '')
        self.meta.sync()
        self.words.sync()
        self.bigrams.sync()
        self.revs.sync()
        self.files.sync()
    sync = synchronized(sync)

    def need_reindex(self):
        return not hasattr(self, 'meta') \
            or self.repo.youngest_rev != \
               int(self.meta.get('last-repo-rev', -1)) \
            or self.env.config.get('repo-search', 'include', '') \
               != self.meta.get('index-include', '') \
            or self.env.config.get('repo-search', 'exclude', '') \
               != self.meta.get('index-exclude', '')
    need_reindex = synchronized(need_reindex)

    def _bigram_search(self, bigrams):
        """ Find all words containing matching bigrams. """
        first_hit = 1
        words = set()
        for bigram in bigrams:
            if bigram in self.bigrams:
                if first_hit:
                    words = self.bigrams[bigram]
                    first_hit = 0
                else:
                    words.intersection_update(set(self.bigrams[bigram]))
            else:
                return ()
        return words
    _bigram_search = synchronized(_bigram_search)

    def _reindex_node(self, node):
        to_unicode = Mimeview(self.env).to_unicode

        def node_tokens():
            content = to_unicode(node.get_content().read(), node.get_content_type())
            for token in self._strip.finditer(content):
                yield token.group().lower()
            for token in self._strip.finditer(node.path):
                yield token.group().lower()

        node_words = set()
        for word in node_tokens():
            if len(word) >= self.minimum_word_length:
                # Split word into bigrams and add to the bigram LUT
                bigrams = self._bigram_word(word)
                for bigram in bigrams:
                    if bigram in self.bigrams:
                        words = set(self.bigrams[bigram])
                        words.add(word)
                        self.bigrams[bigram] = words
                    else:
                        self.bigrams[bigram] = [word]

                # Update word:files mapping
                if word in self.words:
                    files = set(self.words[word])
                    files.add(node.path)
                    self.words[word] = files
                else:
                    self.words[word] = [node.path]
                node_words.add(word)
        self.files[node.path] = node_words
        self.revs[node.path.encode('utf-8')] = unicode(node.rev)
    _reindex_node = _reindex_node

    def _invalidate_file(self, file):
        if file in self.files:
            for word in self.files[file]:
                word_files = self.words[word]
                word_files.discard(file)
                self.words[word] = word_files
            self.env.log.debug("Invalidated stale index entry %s" % file)

    def reindex(self):
        """ Reindex the repository if necessary. """
        if not self.need_reindex():
            return
        start = time.time()
        self.env.log.debug('Indexing repository (either repository or indexing criteria have changed)')
        self._open_storage('c')
        new_files = set()
        for node in TracRepoSearchPlugin(self.env).walk_repo(self.repo):
            if node.kind != Node.DIRECTORY:
                # Node has changed?
                if int(self.revs.get(node.path.encode('utf-8'), -1)) != node.rev:
                    self.env.log.debug("Reindexing %s" % node.path)
                    self._invalidate_file(node.path)
                    self._reindex_node(node)
            new_files.add(node.path)
        
        # All files that don't match the new filter criteria must be purged
        # from the index
        invalidated_files = set(self.files.keys())
        invalidated_files.difference_update(new_files)
        for invalid in invalidated_files:
            self._invalidate_file(invalid)

        self.sync()
        self._open_storage('r')
        self.env.log.debug('Index finished in %.2f seconds' % (time.time() - start))
    reindex = synchronized(reindex)

    def find_words(self, words):
        # First, find all possible words that each search word matches
        all_words = {}
        words = [word.lower() for word in words]
        for word in words:
            word = word.lower()
            bigrams = self._bigram_word(word)
            all_words[word] = set([w for w in self._bigram_search(bigrams)
                                   if word in w])

        # Next, find the intersection of all files that all words appear in
        first_set = 1
        all_files = set()
        for word in words:
            # Find all files that word appears in
            word_files = set()
            for fullword in all_words[word]:
                word_files.update(set(self.words[fullword]))

            if first_set:
                all_files = word_files
                first_set = 0
            else:
                all_files.intersection_update(word_files)
        return all_files
    find_words = synchronized(find_words)
