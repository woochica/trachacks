from trac.core import *
from trac.web.api import IRequestFilter
from trac.ticket.report import ReportModule

from api import PrivateTicketsSystem

__all__ = ['PrivateTicketsReportFilter']

class PrivateTicketsReportFilter(Component):
    """Show only ticket the user is involved in in the reports."""
    
    implements(IRequestFilter)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if isinstance(handler, ReportModule) and \
           not req.perm.has_permission('TICKET_VIEW') and \
           req.args.get('format') in ('tab', 'csv'):
            raise TracError('Access denied')
        return handler
        
    def post_process_request(self, req, template, content_type):
        if req.args.get('DO_PRIVATETICKETS_FILTER') == 'report':            
            # Walk the HDF
            fn = PrivateTicketsSystem(self.env).check_ticket_access
            deleted = []
            left = []
            node = req.hdf.getObj('report.items')
            if node is None:
                return template, content_type
            node = node.child()
            
            while node:
                i = node.name()
                id = req.hdf['report.items.%s.ticket'%i]
                if not fn(req, id):
                    deleted.append(i)
                else:
                    left.append(i)
                node = node.next()
            
            # Delete the needed subtrees
            for n in deleted:
                req.hdf.removeTree('report.items.%s'%n)
                
            # Recalculate this
            req.hdf['report.numrows'] = len(left)
            
            # Move the remaining items into their normal places
            for src, dest in zip(left, xrange(len(left)+len(deleted))):
                if src == dest: continue
                req.hdf.getObj('report.items').copy(str(dest), req.hdf.getObj('report.items.%s'%src))
            for n in xrange(len(left), len(left)+len(deleted)):
                req.hdf.removeTree('report.items.%s'%n)
            
        return template, content_type
