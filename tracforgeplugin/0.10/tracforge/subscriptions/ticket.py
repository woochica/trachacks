# Ticket subscription module

from trac.core import *
from trac.ticket.api import ITicketChangeListener
from trac.ticket.model import Ticket
from trac.web.api import IRequestFilter
from trac.web.main import RequestDispatcher

from api import *
from util import *
from manager import SubscriptionManager

import pickle

class TicketSubscribable(Component):
    """A class implementing ticket subscription."""
    
    implements(ISubscribable, ITicketChangeListener, IRequestFilter)
    
    def __init__(self):
        # Ensure that our custom field exists
        config = self.config['ticket-custom']
        config_changed = False
        
        def add_field(name):
            if name not in config:
                self.log.info('TicketSubscribable: Creating custom %s ticket field'%name)
                config.set(name,'text')
                #config.set(name+'.skip','True') # This doesn't work, see RequestFilter methods
                config_changed = True
        add_field('tracforge_linkmap')

        current_filters = self.config.get('trac','request_filters','').split(',')
        if 'TicketSubscribable' not in current_filters:
            self.log.info('TicketSubscribable: Adding TicketSubscribable to request_filters')
            current_filters.append(self.__class__.__name__)
            self.config.set('trac','request_filters',','.join(current_filters))
            config_changed = True
            
        if config_changed:
            self.config.save()
    
    # ISubscribable methods
    def subscribable_types(self):
        yield 'ticket'
        
    # ITicketChangeListener methods
    def ticket_created(self, ticket):
        linkmap = {}
    
        ticket_copy = Ticket(self.env, ticket.id)
        ticket_copy['tracforge_linkmap'] = serialize_map({self.env.path: ticket.id})

        subscribers = SubscriptionManager(self.env).get_subscribers('ticket')
        for subscriber in subscribers:
            env = open_env(subscriber)
            self.log.debug('Pushing ticket number %s to %s'%(ticket_copy.id,env.path))
            id = TicketSubscribable(env)._ticket_created(ticket_copy)
            linkmap[env.path] = id
            
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        self.log.debug('value = %s' % serialize_map(linkmap))
        cursor.execute("UPDATE ticket_custom SET value=%s "
                       "WHERE ticket = %s AND name = %s" , (serialize_map(linkmap), ticket.id, 'tracforge_linkmap'))
                       
        db.commit()
        
    def ticket_changed(self, ticket, comment, old_values):
        import sys
        frame = sys._getframe(1)
        locals = frame.f_locals
        
        author = locals['author']
        when = locals['when']
        cnum = locals['cnum']
    
        if ticket['tracforge_linkmap']:
            linkmap = unserialize_map(ticket['tracforge_linkmap'])
            for source, id in linkmap.items():
                env = open_env(source)
                TicketSubscribable(env)._ticket_changed(ticket, author, comment, cnum, when, old_values, id)
       
    def ticket_deleted(self, ticket):
        pass
        
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler # Pass-through
        
    def post_process_request(self, req, template, content_type):
        prefix = None
        if req.path_info.startswith('/ticket'):
            prefix = 'ticket'
        elif req.path_info.startswith('/newticket'):
            prefix= 'newticket'
        if prefix:
            hdf = req.hdf.getObj(prefix+'.fields')
            node = hdf.child()
            while node:
                if node.name().startswith('tracforge'):
                    req.hdf['%s.fields.%s.skip'%(prefix,node.name())] = False
                node = node.next()
        
        return (template, content_type)
        
    # Internal methods
    def _ticket_created(self, ticket):
        """Recieve a ticket from another env. It should have the {{{tracforge_linkmap}}} field set."""
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
        return tkt_id

    def _ticket_changed(self, ticket, author, comment, cnum, when, old_values, local_id):
        my_ticket = Ticket(self.env, local_id)
        for f in ticket.fields:
            if not f['name'].startswith('tracforge'):
                my_ticket[f['name']] = ticket[f['name']]
            
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        # Code from trac.ticket.model:225
        custom_fields = [f['name'] for f in my_ticket.fields if f.get('custom')]
        for name in my_ticket._old.keys():
            if name in custom_fields:
                cursor.execute("SELECT * FROM ticket_custom " 
                               "WHERE ticket=%s and name=%s", (my_ticket.id, name))
                if cursor.fetchone():
                    cursor.execute("UPDATE ticket_custom SET value=%s "
                                   "WHERE ticket=%s AND name=%s",
                                   (my_ticket[name], my_ticket.id, name))
                else:
                    cursor.execute("INSERT INTO ticket_custom (ticket,name,"
                                   "value) VALUES(%s,%s,%s)",
                                   (my_ticket.id, name, my_ticket[name]))
            else:
                cursor.execute("UPDATE ticket SET %s=%%s WHERE id=%%s" % name,
                               (my_ticket[name], my_ticket.id))
            cursor.execute("INSERT INTO ticket_change "
                           "(ticket,time,author,field,oldvalue,newvalue) "
                           "VALUES (%s, %s, %s, %s, %s, %s)",
                           (my_ticket.id, when, author, name, my_ticket._old[name],
                            my_ticket[name]))
        # always save comment, even if empty (numbering support for timeline)
        cursor.execute("INSERT INTO ticket_change "
                       "(ticket,time,author,field,oldvalue,newvalue) "
                       "VALUES (%s,%s,%s,'comment',%s,%s)",
                       (my_ticket.id, when, author, cnum, comment))

        cursor.execute("UPDATE ticket SET changetime=%s WHERE id=%s",
                       (when, my_ticket.id))        
        
        db.commit()
