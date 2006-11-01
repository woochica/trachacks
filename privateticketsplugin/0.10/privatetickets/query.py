from trac.core import *
from trac.web.api import IRequestFilter
from trac.ticket.query import QueryModule

from api import PrivateTicketsSystem

__all__ = ['PrivateTicketsQueryFilter']

class PrivateTicketsQueryFilter(Component):
    """Remove entires from queries if this user shouldn't see them."""
    
    implements(IRequestFilter)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
      
    def post_process_request(self, req, template, content_type):
        if req.args.get('DO_PRIVATETICKETS_FILTER') == 'query':
            # Extract the data
            results = []
            node = req.hdf.getObj('query.results')
            if not node:
                return template, content_type
            node = node.child()
            
            while node:
                data = {}
                sub_node = node.child()
                while sub_node:
                    data[sub_node.name()] = sub_node.value()
                    sub_node = sub_node.next()
                results.append(data)
                node = node.next()
                
            self.log.debug('PrivateTickets: results = %r', results)
            # Nuke the old data
            req.hdf.removeTree('query.results')
            
            # Filter down the data
            fn = PrivateTicketsSystem(self.env).check_ticket_access
            new_results = [d for d in results if fn(req, d['id'])]
            
            self.log.debug('PrivateTickets: new_results = %r', new_results)
            
            # Reinsert the data
            req.hdf['query.results'] = new_results
                
        return template, content_type
