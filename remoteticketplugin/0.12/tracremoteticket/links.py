from trac.core import Component, implements
from trac.ticket.api import (ITicketChangeListener, ITicketManipulator, 
                             TicketSystem)

class RemoteLinksProvider(Component):
    
    implements(ITicketChangeListener,
               ITicketManipulator)

    # ITicketChangeListener methods
    def ticket_created(self, ticket): 
        pass
        
    def ticket_changed(self, ticket):
        pass
        
    def ticket_deleted(self, ticket): 
        pass
    
    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions): 
        pass
    
    def validate_ticket(self, req, ticket):
        action = req.args.get('action')
        return []
