'''
Created on Aug 24, 2009

@author: bart
'''

from trac.core import *
from trac.ticket.api import ITicketChangeListener
from model import *

class BacklogTicketChangeListener(Component):
    '''
    listens to the changes of tickets and updates backlogs if necessary 
    '''
    implements(ITicketChangeListener)
    
    # ITicketChangeListener methods
    
    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        
        backlog_name = ticket.values['backlog']
        if(backlog_name != NO_BACKLOG):
            Backlog(self.env, name=backlog_name).add_ticket(ticket.id)

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified.
        
        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """
        
        self.env.log.info('ticket.values = %s;  old_values = %s'%(ticket.values, old_values))
        
        backlog_name = ticket.values.get('backlog',NO_BACKLOG)
        
        # backlog has been changed        
        if('backlog' in old_values.keys()):
            if(backlog_name == NO_BACKLOG):
                Backlog(self.env, name=old_values['backlog']).delete_ticket(ticket.id)
            else:
                Backlog(self.env, name=backlog_name).add_ticket(ticket.id)
        
        # ticket reopened, but backlog not changed.                
        if(old_values.get('status') == 'closed'):
            Backlog(self.env, name=backlog_name).reset_priority(ticket.id, only_if_deleted = True)            
            
        

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        
        print 'ticket_deleted'
        backlog_name = ticket.values['backlog']
        if(backlog_name != NO_BACKLOG):
            Backlog(self.env, name=old_values['backlog']).delete_ticket(ticket.id)

        