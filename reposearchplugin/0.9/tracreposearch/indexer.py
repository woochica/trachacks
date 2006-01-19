"""

Indexing engine for Trac's repository. Implemented using the algorithm
described at:

    http://mail.zope.org/pipermail/zope/2000-April/107218.html

"""

from trac.core import TracError
from tracreposearch.search import TracRepoSearchPlugin
from tracreposearch.lock import lock, unlock, LOCK_EX
from trac.versioncontrol.api import Node
import anydbm
import re
from os.path import pathsep
import os

try:
    set()
except:
    from sets import Set as set

class dbdict(object):
    """ Wrapper around anydbm to transparently allow lists to be stored as
        values. """

    def __init__(self, file, mode):
        self.dbm = anydbm.open(file, mode)

    def __contains__(self, key):
        return key in self.dbm

    def __getitem__(self, key):
       return self.dbm[key].split(pathsep)

    def __setitem__(self, key, value):
        self.dbm[key] = pathsep.join(value)

    def __delitem__(self, key):
        del self.dbm[key]

    def keys(self):
        return self.dbm.keys()

    def sync(self):
        self.dbm.sync()

index_lock = None
lock_count = 0

def acquire_lock():
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
    _strip = re.compile(r'\w+')

    def __init__(self, env):
        self.env = env
        self.repo = self.env.get_repository()

        if not self.env.config.get('repo-search', 'index'):
            raise TracError("Repository search plugin indexer is not " \
                            "configured correctly. Set the 'index' option " \
                            "under the 'repo-search' section to the full " \
                            "(writable) path to the index.")


        self.index_dir = self.env.config.get('repo-search', 'index')
        self.minimum_word_length = int(self.env.config.get('repo-search', 'minimum-word-length', 3))

        if not os.path.isdir(self.index_dir):
            os.mkdir(self.index_dir)

        try:
            self._open_storage('r')
        except:
            self.reindex()

    def _open_storage(self, mode):
        self.meta = anydbm.open(os.path.join(self.index_dir, 'meta.db'), mode)
        self.words = dbdict(os.path.join(self.index_dir, 'words.db'), mode)
        self.bigrams = dbdict(os.path.join(self.index_dir, 'bigrams.db'), mode)
    _open_storage = synchronized(_open_storage)

    def _bigram_word(self, word):
        for start in range(0, len(word) - 1):
            yield word[start:start + 2]

    def sync(self, repo):
        self.meta['last-repo-rev'] = str(repo.youngest_rev)
        self.meta['index-include'] = self.env.config.get('repo-search', 'include', '')
        self.meta['index-exclude'] = self.env.config.get('repo-search', 'exclude', '')
        self.meta.sync()
        self.words.sync()
        self.bigrams.sync()
    sync = synchronized(sync)

    def need_reindex(self, repo):
        result = not hasattr(self, 'meta') or \
            repo.youngest_rev != int(self.meta.get('last-repo-rev', -1)) \
            or self.env.config.get('repo-search', 'include', '1') \
               != self.meta.get('index-include', '') \
            or self.env.config.get('repo-search', 'exclude', '') \
               != self.meta.get('index-exclude', '1')
        return result
    need_reindex = synchronized(need_reindex)

    def _bigram_search(self, bigrams):
        """ Find all words matching bigrams. """
        first_hit = 1
        words = set()
        for bigram in bigrams:
            if bigram in self.bigrams:
                if first_hit:
                    words = set(self.bigrams[bigram])
                    first_hit = 0
                else:
                    words.intersection_update(set(self.bigrams[bigram]))
            else:
                return ()
        return words
    _bigram_search = synchronized(_bigram_search)

    def reindex_node(self, node):
        def node_tokens():
            for token in self._strip.finditer(node.get_content().read()):
                yield token.group().lower()
            for token in self._strip.finditer(node.path):
                yield token.group().lower()

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
    reindex_node = synchronized(reindex_node)

    def reindex(self, repo = None):
        repo = repo or self.env.get_repository()

        if self.need_reindex(repo):
            self.env.log.debug('Indexing repository (either repository or indexing criteria have changed)')
            self._open_storage('n')
            for node in TracRepoSearchPlugin(self.env).walk_repo(repo):
                if node.kind != Node.DIRECTORY:
                    self.reindex_node(node)

            self.sync(repo)
            self._open_storage('r')
            self.env.log.debug('Index finished')
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
