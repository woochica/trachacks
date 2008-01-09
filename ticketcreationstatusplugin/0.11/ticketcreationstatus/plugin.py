from trac.core import Component, implements
from trac.ticket.api import ITicketChangeListener
from trac.config import Option

class TicketCreationStatus(Component):
    implements(ITicketChangeListener)
    
    default_status = Option('ticketcreationstatus', 'default', None, 
        doc="""Determines the status for tickets (if not otherwise modified).""")

    owned_status = Option('ticketcreationstatus', 'owned', None, 
        doc="""Determines the status for tickets that start out owned.""")

    def ticket_created(self, ticket):
        status = None
        if self.owned_status:     
            if ticket['owner']:
                status = self.owned_status

        if not status and self.default_status:
            status = self.default_status

        if status is not None:
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("update ticket set status=%s where id=%s", (status, ticket.id))
            db.commit()

    def ticket_changed(self, ticket, comment, author, old_values):
        pass

    def ticket_deleted(self, ticket):
        pass 