from trac.core import *
from trac.Search import ISearchSource
from trac.ticket.api import TicketSystem
from trac.web.api import IRequestFilter

from api import PrivateTicketsSystem

__all__ = ['PrivateTicketsSearchModule']

class PrivateTicketsSearchModule(Component):
    """Search restricted to tickets you are involved with."""

    implements(ISearchSource, IRequestFilter)
    
    # ISearchSource methods
    def get_search_filters(self, req):
        if not req.perm.has_permission('TICKET_VIEW') and \
           ( req.perm.has_permission('TICKET_VIEW_REPORTER') or \
             req.perm.has_permission('TICKET_VIEW_CC') or \
             req.perm.has_permission('TICKET_VIEW_ASSIGNED')
           ):
            yield ('pticket', 'Tickets')
            
    def get_search_results(self, req, terms, filters):
        if req.perm.has_permission('TICKET_VIEW'): return
        if 'pticket' not in filters: return
        
        req._MUNGE_FILTER = True
        fn = PrivateTicketsSystem(self.env).check_ticket_access
        
        for result in TicketSystem(self.env).get_search_results(req, terms, ['ticket']):
            id = int(result[0].split('/')[-1])
            self.log.debug('PrivateTicketsSearchModule: Check id %r', id)
            if fn(req, id):
                yield result

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
        
    def post_process_request(self, req, template, content_type):
        if hasattr(req, '_MUNGE_FILTER'):
            node = req.hdf.getObj('search.filters').child()
            while node:
                if req.hdf['search.filters.%s.name'%node.name()] == 'pticket':
                    req.hdf['search.filters.%s.name'%node.name()] = 'ticket'
                node = node.next()
               
        return template, content_type
