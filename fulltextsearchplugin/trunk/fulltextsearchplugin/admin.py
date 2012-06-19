import sys

from trac.admin import AdminCommandError, IAdminCommandProvider, PrefixList
from trac.core import Component, implements
from trac.util.translation import _
from trac.util.text import printout, print_table

from fulltextsearchplugin.fulltextsearch import FullTextSearch

class FullTextSearchAdmin(Component):
    """trac-admin command provider for full text search administration.
    """
    implements(IAdminCommandProvider)

    # IAdminCommandProvider methods

    def get_admin_commands(self):
        yield ('fulltext index', '[realm]',
               """Index Trac resources that are out of date
               
               When [realm] is specified, only that realm is updated.
               Synchronises the search index with Trac by indexing resources
               that have been added or updated.
               """,
               self._complete_admin_command, self._do_index)
        yield ('fulltext list', '[realm]',
               """List Trac resources that are indexed.
               
               When [realm] is specified, only that realm is listed.
               """,
               self._complete_search_command, self._do_list)
        yield ('fulltext optimize', '',
               """Optimize the search index by merging segments and removing
               stale documents
               
               Optimizing should be performed infrequently (e.g. nightly), if
               at all, since it is very expensive and involves reading and
               re-writing the entire index. NB: if multiple projects share
               an index this will operation will affect all of them.
               """,
               None, self._do_optimize)
        yield ('fulltext reindex', '[realm]',
               """Re-index all Trac resources.
               
               When [realm] is specified, only that realm is re-indexed.
               Discards the search index and recreates it. Note that this
               operation can take a long time to complete. If indexing gets
               interrupted, it can be resumed later using the `index` command.
               """,
               self._complete_admin_command, self._do_reindex)
        yield ('fulltext remove', '[realm]',
               """Remove the search index, or part of it
               
               When [realm] is specified, only that realm is removed from the
               index.
               """,
               self._complete_admin_command, self._do_remove)

    def _complete_admin_command(self, args):
        fts = FullTextSearch(self.env)
        if len(args) == 1:
            return PrefixList(fts.index_realms)

    def _complete_search_command(self, args):
        fts = FullTextSearch(self.env)
        if len(args) == 1:
            return PrefixList(fts.search_realms)

    def _index(self, realm, clean):
        fts = FullTextSearch(self.env)
        realms = realm and [realm] or fts.index_realms
        if clean:
            printout(_("Wiping search index and re-indexing all items in "
                       "realms: %(realms)s", realms=fts._fmt_realms(realms)))
        else:
            printout(_("Indexing new and changed items in realms: %(realms)s",
                       realms=fts._fmt_realms(realms)))
        fts.index(realms, clean, self._index_feedback, self._clean_feedback)
        printout(_("Indexing finished"))

    def _index_feedback(self, realm, resource):
        #sys.stdout.write('\r\x1b[K %s' % (resource,))
        sys.stdout.flush()

    def _clean_feedback(self, realm, resource):
        #sys.stdout.write('\r\x1b[K')
        sys.stdout.flush()

    def _do_index(self, realm=None):
        self._index(realm, clean=False)

    def _do_list(self, realm=None):
        fts = FullTextSearch(self.env)
        realms = realm and [realm] or fts.index_realms
        fields = ['realm', 'id']
        query, response = fts._do_search('*', realms, sort_by=fields,
                                         field_limit=fields)
        rows = ((doc['realm'], doc['id']) for doc in fts._docs(query))
        print_table(rows, (_("Realm"), _("Id")))

    def _do_optimize(self):
        fts = FullTextSearch(self.env)
        fts.optimize()

    def _do_reindex(self, realm=None):
        self._index(realm, clean=True)

    def _do_remove(self, realm=None):
        fts = FullTextSearch(self.env)
        realms = realm and [realm] or fts.index_realms
        fts.remove_index(realms)

