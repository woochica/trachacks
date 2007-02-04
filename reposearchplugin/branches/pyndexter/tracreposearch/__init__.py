import re
import posixpath
import os
import pyndexter
import pickle
from fnmatch import fnmatch
from trac.core import *
from trac.config import *
from trac.Search import ISearchSource, shorten_result
from trac.versioncontrol.api import Node
from trac.perm import IPermissionRequestor
from trac.util import Markup, escape
from trac.mimeview.api import Mimeview

try:
    set
except:
    from sets import Set as set


class RepoSource(pyndexter.Source):
    """Pyndexter Source for SVN the Trac SVN abstraction layer."""

    def __init__(self, env, framework, repo, include=None, exclude=None):
        pyndexter.Source.__init__(self, framework, include, exclude)
        self.env = env
        self.repo = repo

    def matches(self, uri):
        return True

    def __hash__(self):
        return 1

    def fetch(self, uri):
        node = self.repo.get_node(uri)
        def fetch_content(uri):
            content = Mimeview(self.env).to_unicode(node.get_content().read(),
                                                 node.get_content_type())
            return content

        return pyndexter.Document(content=fetch_content, uri=uri, rev=node.rev,
                                  mimetype=node.get_content_type(),
                                  source=self, changed=node.rev)

    def exists(self, uri):
        try:
            self.repo.get_node(uri)
            return True
        except:
            return False

    def marshal(self, file):
        pickle.dump({'rev': self.repo.youngest_rev, 'include': self.include,
                     'exclude': self.exclude}, file)

    def difference(self, file):
        try:
            state = pickle.load(file)
        except pickle.PickleError, e:
            raise pyndexter.InvalidState('Invalid state provided to TracRepoSource. '
                                         'Exception was %s: %s' % (e.__class__.__name__, e))

        last_rev = state['rev']

        if last_rev == self.repo.youngest_rev:
            return

        old_set = set([node.path for node in self._walk_repository(state['rev'])])
        new_set = set()

        for node in self._walk_repository():
            if node.path not in old_set:
                yield (pyndexter.ADDED, node.path)
            elif node.rev != self.repo.get_node(node.path, last_rev).rev:
                yield (pyndexter.MODIFIED, node.path)
            new_set.add(node.path)

        for removed in old_set.difference(new_set):
            yield (pyndexter.REMOVED, removed)

    def __iter__(self):
        for node in self._walk_repository():
            yield node.path

    # Internal methods
    def _fetch_content(self, uri):
        return self.repo.get_node(uri).get_content().read()

    def _walk_repository(self, rev=None):
        def searchable(path):
            # Exclude paths
            for exclude in self.exclude:
                if fnmatch(path, exclude):
                    return 0

            # Include paths
            for include in self.include:
                if fnmatch(path, include):
                    return 1

            return not self.include

        def do_walk(path):
            node = self.repo.get_node(path, rev)
            basename = posixpath.basename(path)

            if node.kind == Node.DIRECTORY:
                for subnode in node.get_entries():
                    for result in do_walk(subnode.path):
                        yield result
            elif searchable(node.path):
                yield node


        for node in do_walk('/'):
            yield node




class TracRepoSearchPlugin(Component):
    """ Search the source repository. """
    implements(ISearchSource, IPermissionRequestor)

    indexer = Option('repo-search', 'indexer', doc='Pyndexter indexer URI to use')
    includes = ListOption('repo-search', 'include', sep=os.path.pathsep,
                          doc='List of paths to globs to include in the index')
    excludes = ListOption('repo-search', 'exclude', sep=os.path.pathsep,
                          doc='List of paths to globs to exclude from the index')

    def __init__(self):
        self.repo = self.env.get_repository()
        self.framework = pyndexter.Framework(self.indexer)
        self.framework.add_source(RepoSource(self.env, self.framework, self.repo,
                                             self.includes, self.excludes))

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'REPO_SEARCH'

    # ISearchSource methods
    def get_search_filters(self, req):
        if req.perm.has_permission('REPO_SEARCH'):
            yield ('repo', 'Source Repository', 0)

    def get_search_results(self, req, query, filters):
        if 'repo' not in filters or not req.perm.has_permission('REPO_SEARCH'):
            return

        if not self.indexer:
            raise TracError('RepoSearch plugin not configured correctly. '
                            'You need to set "repo-search.indexer".')

        db = self.env.get_db_cnx()
        to_unicode = Mimeview(self.env).to_unicode

        self._update_index()

        for hit in self.framework.search(' '.join(query)):
            node = self.repo.get_node(hit.uri)
            change = self.repo.get_changeset(node.rev)
            if node.kind == Node.DIRECTORY:
                yield (self.env.href.browser(node.path),
                       node.path, change.date, change.author,
                       'Directory')
            else:
                found = 0
                content = to_unicode(node.get_content().read(), node.get_content_type())
                for n, line in enumerate(content.splitlines()):
                    line = line.lower()
                    for q in query:
                        idx = line.find(q)
                        if idx != -1:
                            found = n + 1
                            break
                    if found:
                        break

                yield (self.env.href.browser(node.path) + (found and '#L%i' % found or ''),
                       node.path, change.date, change.author,
                       shorten_result(content, query))

    # Internal methods
    def _update_index(self):
        def logging_filter(context, stream):
            for transition, uri in stream:
                self.env.log.debug('Updating index %s, %s' % (transition, uri))
                yield transition, uri

        self.framework.update(filter=logging_filter)
        self.framework.sync()
