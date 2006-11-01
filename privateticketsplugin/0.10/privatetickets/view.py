from trac.core import *
from trac.web.chrome import INavigationContributor
from trac.ticket.web_ui import TicketModule
from trac.ticket.query import QueryModule
from trac.Search import SearchModule
from trac.ticket.report import ReportModule

from api import PrivateTicketsSystem

__all__ = ['PrivateTicketsViewModule']

class PrivateTicketsViewModule(Component):
    """Allow users to see tickets they are involved in."""
    
    implements(INavigationContributor)
    
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return ''
        
    def get_navigation_items(self, req):
        # Don't allow this to be exposed
        if 'DO_PRIVATETICKETS_FILTER' in req.args.keys():
            del req.args['DO_PRIVATETICKETS_FILTER']
        
        # Various ways to allow access
        if not req.perm.has_permission('TICKET_VIEW'):
            if TicketModule(self.env).match_request(req):
                if PrivateTicketsSystem(self.env).check_ticket_access(req, req.args['id']):
                    self._grant_view(req)
            elif QueryModule(self.env).match_request(req):
                req.args['DO_PRIVATETICKETS_FILTER'] = 'query'
                self._grant_view(req) # Further filtering in query.py
            elif SearchModule(self.env).match_request(req):
                if 'ticket' in req.args.keys():
                    req.args['pticket'] = req.args['ticket']
                    del req.args['ticket']
            elif ReportModule(self.env).match_request(req):
                self._grant_view(req) # So they can see the query page link
                if req.args.get('id'):
                    req.args['DO_PRIVATETICKETS_FILTER'] = 'report'
        return []

    # Internal methods
    def _grant_view(self, req):
        req.perm.perms['TICKET_VIEW'] = True
        req.hdf['trac.acl.TICKET_VIEW'] = 1
