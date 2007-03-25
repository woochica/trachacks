from trac.core import *
from tracrpc.api import IXMLRPCHandler
from trac.Search import ISearchSource

try:
    a = set()
except:
    from sets import Set as set

class SearchRPC(Component):
    """ Search Trac. """
    implements(IXMLRPCHandler)

    search_sources = ExtensionPoint(ISearchSource)

    # IXMLRPCHandler methods
    def xmlrpc_namespace(self):
        return 'search'

    def xmlrpc_methods(self):
        yield ('SEARCH_VIEW', ((list,),), self.getSearchFilters)
        yield ('SEARCH_VIEW', ((list, str), (list, str, list)), self.performSearch)

    # Others
    def getSearchFilters(self, req):
        """ Retrieve a list of search filters with each element in the form
            (name, description). """
        for source in self.search_sources:
            for filter in source.get_search_filters(req):
                yield filter

    def performSearch(self, req, query, filters = []):
        """ Perform a search using the given filters. Defaults to all if not
            provided. Results are returned as a list of tuples in the form
           (href, title, date, author, excerpt)."""
        from trac.Search import search_terms
        query = search_terms(query)
        chosen_filters = set(filters)
        available_filters = []
        for source in self.search_sources:
            available_filters += source.get_search_filters(req)

        filters = [f[0] for f in available_filters if f[0] in chosen_filters]
        if not filters:
            filters = [f[0] for f in available_filters]
        self.env.log.debug("Searching with %s" % filters)

        results = []
        for source in self.search_sources:
            for result in source.get_search_results(req, query, filters):
                result = map(unicode, result)
                results.append(['/'.join(req.base_url.split('/')[0:3])
                                + result[0]] + list(result[1:]))
        return results
