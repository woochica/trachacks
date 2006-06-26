# Ticket subscription module

from trac.core import *
from trac.ticket.api import ITicketChangeListener
from trac.ticket.model import Ticket

from api import *
from util import *
from manager import SubscriptionManager

class TicketSubscribable(Component):
    """A class implementing ticket subscription."""
    
    implements(ISubscribable, ITicketChangeListener)
    
    def __init__(self):
        # Ensure that our custom field exists
        config = self.config['ticket-custom']
        if 'tracforge_source' not in config:
            self.log.info('TicketSubscribable: Creating custom ticket field')
            config.set('tracforge_source','text')
            #config.set('tracforge_source.skip','True') # This doesn't work
            self.config.save()
    
    # ISubscribable methods
    def subscribable_types(self):
        yield 'ticket'

    # ITicketChangeListener methods
    def ticket_created(self, ticket):
        ticket_copy = Ticket(self.env, ticket.id)
        ticket_copy['tracforge_source'] = self.env.path

        subscribers = SubscriptionManager(self.env).get_subscribers('ticket')
        for subscriber in subscribers:
            env = open_env(subscriber)
            self.log.debug('Pushing ticket number %s to %s'%(ticket_copy.id,env.path))
            ts = TicketSubscribable(env)._ticket_created(ticket_copy)
        
    def ticket_changed(self, ticket, comment, old_values):
        pass
       
    def ticket_deleted(self, ticket):
        pass

    # Internal methods
    def _ticket_created(self, ticket):
        """Recieve a ticket from another env. It should have the {{{tracforge_source}}} field set."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # TODO: SubscriptionFilters check should go here

        # Ticket insertion code from trac.ticket.model:134 r3464
        # TODO: This should somehow use Ticket.insert() directly, though beware of subscription loops
        # Insert ticket record
        std_fields = [f['name'] for f in ticket.fields if not f.get('custom')
                      and ticket.values.has_key(f['name'])]
        cursor.execute("INSERT INTO ticket (%s,time,changetime) VALUES (%s)"
                       % (','.join(std_fields),
                          ','.join(['%s'] * (len(std_fields) + 2))),
                       [ticket[name] for name in std_fields] +
                       [ticket.time_created, ticket.time_changed])
        tkt_id = db.get_last_id(cursor, 'ticket')

        # Insert custom fields
        custom_fields = [f['name'] for f in ticket.fields if f.get('custom')
                         and ticket.values.has_key(f['name'])]
        if custom_fields:
            cursor.executemany("INSERT INTO ticket_custom (ticket,name,value) "
                               "VALUES (%s,%s,%s)", [(tkt_id, name, ticket[name])
                                                     for name in custom_fields])
        db.commit()
