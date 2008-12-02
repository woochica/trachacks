from trac.core import Component, implements
from trac.ticket.api import ITicketChangeListener

#local
from notification import SpecialTicketNotifyEmail

class TicketTeamDispatcher(Component):
    implements(ITicketChangeListener)

    def ticket_created(self, ticket):
        mail = SpecialTicketNotifyEmail(self.env)
        mail.notify(ticket)

    def ticket_changed(self, ticket, comment, author, old_values):
        pass

    def ticket_deleted(self, ticket):
        pass 
