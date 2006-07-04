# Restricted ticket entry module

from trac.core import *
from trac.web.chrome import INavigationContributor
from trac.web import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.util import Markup

from trac.ticket.web_ui import NewticketModule

class SimpleTicketModule(Component):
    """Restricted ticket entry form."""
    
    implements(IRequestHandler, INavigationContributor, IPermissionRequestor)
    
    # INavigationContributer methods
    def get_active_navigation_item(self, req):
        return 'simpleticket'
        
    def get_navigation_items(self, req):
        if req.perm.has_permission('TICKET_CREATE_SIMPLE') and \
           not req.perm.has_permission('TICKET_CREATE'):
            yield ('mainnav', 'simpleticket', Markup('<a href="%s" accesskey="7">New Ticket</a>',self.env.href.simpleticket()))
            
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/simpleticket')
        
    def process_request(self, req):
        req.perm.assert_permission('TICKET_CREATE_SIMPLE')
    
        # Force TICKET_CREATE
        really_has_perm = req.perm.has_permission('TICKET_CREATE')
        req.perm.perms['TICKET_CREATE'] = True
        
        # Find which fields to not show
        hide_fields = [x.strip() for x in self.config.get('simpleticket','hide', default='').split(',') if x.strip()]

        # Process the request via the original newticket module
        template, content_type = NewticketModule(self.env).process_request(req)
        
        # Hide the fields
        for f in hide_fields:
            req.hdf['newticket.fields.%s.skip'%f] = True
        
        # Restore TICKET_CREATE
        if not really_has_perm:
            del req.perm.perms['TICKET_CREATE']
            
        return (template, content_type)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'TICKET_CREATE_SIMPLE'


