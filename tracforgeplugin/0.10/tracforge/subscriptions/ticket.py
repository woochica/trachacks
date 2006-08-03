# Ticket subscription module

from trac.core import *
from trac.ticket.api import ITicketChangeListener
from trac.ticket.model import Ticket
from trac.web.api import IRequestFilter
from trac.web.main import RequestDispatcher

from api import *
from util import *
from manager import SubscriptionManager

# Python 2.3 compat
try:
    set = set
except NameError:
    from sets import Set as set

class TicketOldValues(object):

    _history = {}
    
    def history(self, instance):
        key = id(instance)
        if key not in self._history:
            self._history[key] = [None]
        return self._history[key]
        
    def real_old_values(self, instance):
        return self.history(instance)[-2]
       
    def __get__(self, instance, owner):
        if instance == None:
            return self
        return self.history(instance)[-1]
        
    def __set__(self, instance, value):
        self.history(instance).append(value)
        return self.history(instance)[-1]
        
    def __del__(self, instance):
        self.history(instance).append(None)

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
            
        # Evil things
        Ticket._old = TicketOldValues()
    
    # ISubscribable methods
    def subscribable_types(self):
        yield 'ticket'
        
    # ITicketChangeListener methods
    def ticket_created(self, ticket):
        # Check for loops
        if self._check_ticket(ticket): return
        
        linkmap = {}
    
        ticket_copy = Ticket(self.env, ticket.id)
        ticket_copy['tracforge_linkmap'] = serialize_map({self.env.path: ticket.id})
        ticket_copy.tracforge_seen = ticket.tracforge_seen

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
        self.log.debug("TicketSubscribable: In ticket_changed(%s) for '%s'"%(ticket.id,self.env.path))
        # Check for loops
        if self._check_ticket(ticket):
            self.log.debug('TicketSubscribable: Duplicate, bailing!')
            return
        self.log.debug("TicketSubscribable: seen = %s"%ticket.tracforge_seen)
        
        # Start evil things (if you aren't me, just skip over this part)
        import sys
        frame = sys._getframe(1)
        locals = frame.f_locals
        
        author = locals['author']
        when = locals['when']
        cnum = locals['cnum']
        
        old_values = Ticket._old.real_old_values(ticket)
        # End evil things
        
        if ticket['tracforge_linkmap']:
            linkmap = unserialize_map(ticket['tracforge_linkmap'])
            for source, id in linkmap.items():
                env = open_env(source)
                if env.path in ticket.tracforge_seen:
                    continue # Been there, done that
                self.log.debug('TicketSubscribable: Propagating change to %s'%env.path)
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
                    req.hdf['%s.fields.%s.skip'%(prefix,node.name())] = True
                node = node.next()
        
        return (template, content_type)
        
    # Internal methods
    def _ticket_created(self, ticket):
        """Recieve a ticket from another env. It should have the {{{tracforge_linkmap}}} field set."""

        # TODO: SubscriptionFilters check should go here

        ticket.id = None # Clear out the ID
        db = self.env.get_db_cnx()
        ticket.insert(ticket.time_created, db)
        db.commit()
        return ticket.id
        
    def _ticket_changed(self, ticket, author, comment, cnum, when, old_values, local_id):
        self.log.debug('TicketSubscribable: In _ticket_changed(%s,local=%s) for %s'%(ticket.id, local_id, self.env.path))
        self.log.debug("TicketSubscribable: seen = %s"%ticket.tracforge_seen)
        my_ticket = Ticket(self.env, local_id)
        my_ticket.tracforge_seen = ticket.tracforge_seen
        for f in old_values:
            if not f.startswith('tracforge'):
                my_ticket[f] = ticket[f]
            
        my_ticket.save_changes(author, comment, when, cnum=cnum)

    def _check_ticket(self, ticket):
        # Check for loops
        if not hasattr(ticket, 'tracforge_seen'):
            ticket.tracforge_seen = set()
           
        if self.env.path in ticket.tracforge_seen:
            return True # We have already seen this ticket
        else:
            ticket.tracforge_seen.add(self.env.path)
            return False
