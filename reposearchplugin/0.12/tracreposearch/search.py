from trac.core import *
from trac.search import ISearchSource, shorten_result
from trac.versioncontrol.api import Node
from trac.perm import IPermissionRequestor
from trac.util import Markup, escape
from trac.mimeview.api import Mimeview
import re
import posixpath
import os
from fnmatch import fnmatch

class TracRepoSearchPlugin(Component):
    """ Search the source repository. """
    implements(ISearchSource, IPermissionRequestor)

    def _get_filters(self):
        includes = [glob for glob in self.env.config.get('repo-search',
                   'include', '').split(os.path.pathsep) if glob]
        excludes = [glob for glob in self.env.config.get('repo-search',
                   'exclude', '').split(os.path.pathsep) if glob]
        return (includes, excludes)

    def walk_repo(self, repo):
        """ Walk all nodes in the repo that match the filters. """
        includes, excludes = self._get_filters()

        def searchable(path):
            # Exclude paths
            for exclude in excludes:
                if fnmatch(path, exclude):
                    return 0

            # Include paths
            for include in includes:
                if fnmatch(path, include):
                    return 1

            return not includes

        def do_walk(path):
            node = repo.get_node(path)
            basename = posixpath.basename(path)

            if searchable(node.path):
                yield node

            if node.kind == Node.DIRECTORY:
                for subnode in node.get_entries():
                    for result in do_walk(subnode.path):
                        yield result

        for node in do_walk('/'):
            yield node

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'REPO_SEARCH'

    # ISearchSource methods
    def get_search_filters(self, req):
        if req.perm.has_permission('REPO_SEARCH'):
            yield ('repo', 'Source Repository', 0)

    def get_search_results(self, req, query, filters):
        if 'repo' not in filters:
            return
        repo = self.env.get_repository(authname=req.authname)
        if not isinstance(query, list):
            query = query.split()
        query = [q.lower() for q in query]
        db = self.env.get_db_cnx()
        include, excludes = self._get_filters()

        to_unicode = Mimeview(self.env).to_unicode

        # Use indexer if possible, otherwise fall back on brute force search.
        try:
            from tracreposearch.indexer import Indexer
            self.indexer = Indexer(self.env)
            self.indexer.reindex()
            walker = lambda repo, query: [repo.get_node(filename) for filename
                                          in self.indexer.find_words(query)]
        except TracError, e:
            self.env.log.warning(e)
            self.env.log.warning('Falling back on full repository walk')
            def full_walker(repo, query):
                for node in self.walk_repo(repo):
                    # Search content
                    matched = 1
                    content = node.get_content()
                    if not content:
                        continue
                    content = to_unicode(content.read().lower(), node.get_content_type())
                    for term in query:
                        if term not in content:
                            matched = 0
                            break
                    if matched:
                        yield node

            walker = full_walker

        if not req.perm.has_permission('REPO_SEARCH'):
            return

        def match_name(name):
            for term in query:
                if term not in name:
                    return 0
            return 1

        for node in walker(repo, query):
            change = repo.get_changeset(node.rev)
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
