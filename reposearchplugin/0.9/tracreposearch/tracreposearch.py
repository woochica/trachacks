from trac.core import *
from trac.Search import ISearchSource, shorten_result
from trac.versioncontrol.api import Node
from trac.perm import IPermissionRequestor
from trac.util import Markup
import re
import posixpath

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

        repo = self.env.get_repository(req.authname)

        query = query.split()
        db = self.env.get_db_cnx()

        def walk_repo(path):
            node = repo.get_node(path)
            if node.kind == Node.DIRECTORY:
                for subnode in node.get_entries():
                    for result in walk_repo(subnode.path):
                        yield result
            else:
                # Search name
                basename = posixpath.basename(path)
                match_name = 1
                match_content = 1
                excerpt = None
                for term in query:
                    if term not in basename:
                        match_name = 0
                        break

                # Search content
                content = node.get_content().read()
                for term in query:
                    if term not in content:
                        match_content = 0
                        break
                if not (match_name or match_content):
                    return
                change = repo.get_changeset(node.rev)
                yield (self.env.href.browser(path),
                       path, change.date, change.author,
                       shorten_result(content, query))

        for result in walk_repo('/'):
            yield result
