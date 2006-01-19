from trac.core import *
from trac.Search import ISearchSource, shorten_result
from trac.versioncontrol.api import Node
from trac.perm import IPermissionRequestor
from trac.util import Markup
import re
import posixpath
import os
from fnmatch import fnmatch

class TracRepoSearchPlugin(Component):
    """ Search the source repository. """
    implements(ISearchSource, IPermissionRequestor)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'REPO_SEARCH'

    # ISearchSource methods
    def get_search_filters(self, req):
        if req.perm.has_permission('REPO_SEARCH'):
            yield ('repo', 'Source Repository', 0)

    def get_search_results(self, req, query, filters):
        if not req.perm.has_permission('REPO_SEARCH'):
            return

        includes = [glob for glob in self.env.config.get('repo-search',
                   'include', '').split(os.path.pathsep) if glob]
        excludes = [glob for glob in self.env.config.get('repo-search',
                   'exclude', '').split(os.path.pathsep) if glob]

        repo = self.env.get_repository(req.authname)

        query = query.split()
        db = self.env.get_db_cnx()

        self.env.log.debug(str(includes))
        self.env.log.debug(str(excludes))

        def searchable(path):
            # Exclude paths
            for exclude in excludes:
                if fnmatch(path, exclude):
                    return 0

            # Include paths
            for include in includes:
                if fnmatch(path, include):
                    return 1

            return 1

        def match_name(name):
            for term in query:
                if term not in name:
                    return 0
            return 1

        def walk_repo(path):
            node = repo.get_node(path)
            basename = posixpath.basename(path)

            if node.kind == Node.DIRECTORY:
                if match_name(basename):
                    change = repo.get_changeset(node.rev)
                    yield (self.env.href.browser(path),
                           path, change.date, change.author,
                           'Directory')

                for subnode in node.get_entries():
                    for result in walk_repo(subnode.path):
                        yield result
            else:
                if not searchable(path):
                    return

                # Search content
                match_content = 1
                content = node.get_content().read()
                for term in query:
                    if term not in content:
                        match_content = 0
                        break
                if not (match_name(basename) or match_content):
                    return
                change = repo.get_changeset(node.rev)
                yield (self.env.href.browser(path),
                       path, change.date, change.author,
                       shorten_result(content, query))

        for result in walk_repo('/'):
            yield result
