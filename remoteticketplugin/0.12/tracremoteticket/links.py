from copy import copy
from itertools import groupby
from operator import itemgetter

from trac.core import Component, implements
from trac.resource import ResourceNotFound
from trac.ticket.api import (ITicketChangeListener, ITicketManipulator, 
                             TicketSystem)
from trac.ticket.links import LinksProvider
from trac.ticket.model import Ticket
from trac.util import unique

from tracremoteticket.api import RemoteTicketSystem
from tracremoteticket.model import RemoteTicket

__all__ = ['RemoteLinksProvider']

class RemoteLinksProvider(Component):
    
    implements(ITicketChangeListener,
               ITicketManipulator)
    
    # ITicketChangeListener methods
    def ticket_created(self, ticket):
        self.ticket_changed(ticket, '', ticket['reporter'], None)
        
    def ticket_changed(self, ticket, comment, author, old_values):
        link_fields = [f['name'] for f in ticket.fields if f.get('link')]
        ticket_system = TicketSystem(self.env)
        links_provider = LinksProvider(self.env)
        remote_tktsys = RemoteTicketSystem(self.env)
        
        if not old_values:
            old_values = self._fetch_remote_links(ticket.id)
            
        @self.env.with_transaction()
        def do_changed(db):
            cursor = db.cursor()
            for end in [e for e in link_fields if e in old_values]:
                new_rtkts  = set(remote_tktsys.parse_links(ticket[end]))
                old_rtkts  = set(remote_tktsys.parse_links(old_values[end]))
                
                # New links added
                for remote_name, remote_id in new_rtkts - old_rtkts:
                    cursor.execute('''
                        INSERT INTO remote_ticket_links
                        (source_name, source, type, 
                            destination_name, destination)
                        VALUES (%s, %s, %s, %s, %s)''',
                        ('', ticket.id, end, remote_name, remote_id))
                    other_end = ticket_system.link_ends_map[end]
                    if other_end:
                        cursor.execute('''
                            INSERT INTO remote_ticket_links
                            (source_name, source, type, 
                                destination_name, destination)
                            VALUES (%s, %s, %s, %s, %s)''',
                            (remote_name, remote_id, other_end, '', ticket.id))
                
                # Old links removed
                for remote_name, remote_id in old_rtkts - new_rtkts:
                    cursor.execute('''
                        DELETE FROM remote_ticket_links 
                        WHERE source_name='' AND source=%s AND type=%s
                        AND destination_name=%s AND destination=%s''',
                        (ticket.id, end, remote_name, remote_id))
                    other_end = ticket_system.link_ends_map[end]
                    if other_end:
                        cursor.execute('''
                            DELETE FROM remote_ticket_links 
                            WHERE source_name=%s AND source=%s AND type=%s
                            AND destination_name='' AND destination=%s''',
                            (remote_name, remote_id, other_end, ticket.id))
                
    def ticket_deleted(self, ticket):
        @self.env.with_transaction()
        def do_delete(db):
            cursor = db.cursor()
            cursor.execute('''
                DELETE FROM remote_ticket_links
                WHERE  (source_name='' AND source = %s)
                OR (destination_name='' AND destination = %s)''',
                (ticket.id, ticket.id))
                
    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions): 
        pass
    
    def validate_ticket(self, req, ticket):
        action = req.args.get('action')
        ticket_system = TicketSystem(self.env)
        links_provider = LinksProvider(self.env)
        remote_tktsys = RemoteTicketSystem(self.env)
        
        for end in ticket_system.link_ends_map:
            check = self.validate_links_exist(ticket, end)
            if check:
                yield None, check
                continue
                
            validator_name = links_provider.get_validator(end)
            if validator_name == 'no_cycle':
                validator = self.validate_no_cycle
            elif (validator_name == 'parent_child' 
                  and end == links_provider.PARENT_END):
                validator = self.validate_parent
            else:
                validator = self.validate_any
            
            check = validator(ticket, end)
            if check:
                yield None, check
            
            if action == 'resolve':
                blockers = self.find_blockers(ticket, end, [])
                if blockers:
                    blockers_str = ', '.join('%s' % x 
                                             for x in unique(blockers))
                    msg = ("Cannot resolve this ticket because it is "
                           "blocked by '%s' tickets [%s]" 
                           % (end,  blockers_str))
                    yield None, msg
        
    def validate_links_exist(self, ticket, end):
        remote_tktsys = RemoteTicketSystem(self.env)
        links = remote_tktsys.parse_links(ticket[end])
        bad_links = []
        for remote_name, link in links:
            try:
                tkt = RemoteTicket(self.env, remote_name, link)
            except ResourceNotFound:
                bad_links.append((remote_name, link))
        if bad_links:
            return ("Remote tickets linked in '%s' could not be found: [%s]"
                    % (end, ', '.join('%s:#%s' % t for t in bad_links)))
        
    def validate_no_cycle(self, ticket, end):
        cycle = self.find_cycle(ticket, end, [])
        if cycle != None:
            return ('Cycle in ''%s'': %s' 
                    % (LinksProvider(self.env).render_end(end), 
                       ' -> '.join(cycle)))
                       
    def validate_parent(self, ticket, end):
        cycle_validation = self.validate_no_cycle(ticket, end)
        if cycle_validation: 
            return cycle_validation
        
        links = RemoteTicketSystem(self.env).parse_links(ticket[end])
        if len(links) > 1 and end == LinksProvider.PARENT_END:
            parents_str = ', '.join('%s:#%s' % (remote_name, tkt_id) 
                                    for (remote_name, tkt_id) in links)
            return ("Multiple links in '%s': %s:#%s -> [%s]"
                    % (LinksProvider(self.env).render_end(end),
                       ticket.remote_name, ticket.id, parents_str))
                       
    def validate_any(self, ticket, end):
        return None
    
    def find_blockers(self, ticket, field, blockers):
        tkt_ref = '%s:#%s' % (getattr(ticket, 'remote_name', ''), ticket.id)
        remote_tktsys = RemoteTicketSystem(self.env)
        links = remote_tktsys.parse_links(ticket[field])
        for remote_name, link in links:
            linked_ticket = RemoteTicket(self.env, remote_name, link)
            if linked_ticket['status'] != 'closed':
                blockers.append(tkt_ref)
            else:
                self.find_blockers(linked_ticket, field, blockers)
        return blockers
    
    def find_cycle(self, ticket, field, path):
        tkt_ref = '%s:#%s' % (getattr(ticket, 'remote_name', ''), ticket.id)
        if tkt_ref in path:
            path.append(tkt_ref)
            return path
        
        path.append(tkt_ref)
        
        remote_tktsys = RemoteTicketSystem(self.env)
        links = remote_tktsys.parse_links(ticket[field])
        for remote_name, link in links:
            linked_ticket = RemoteTicket(self.env, remote_name, link)
            cycle = self.find_cycle(linked_ticket, field, copy(path))
            if cycle != None:
                return cycle
        return None
    
    def augment_ticket(self, ticket):
        remote_link_vals = self._fetch_remote_links(ticket.id)
        for end, remote_links in remote_link_vals.items():
            if ticket[end] and remote_links:
                ticket[end] = '%s, %s' % (ticket[end], remote_links)
            elif remote_links:
                ticket[end] = remote_links
        
    def _fetch_remote_links(self, tkt_id):
        link_ends_map =  TicketSystem(self.env).link_ends_map
        db = self.env.get_read_db()
        cursor = db.cursor()
        cursor.execute('''SELECT type, destination_name, destination
                       FROM remote_ticket_links
                       WHERE type IN (%s) AND source_name='' and source=%%s
                       ORDER BY type, destination_name, destination
                       ''' % (','.join(['%s'] * len(link_ends_map))),
                       list(link_ends_map) + [tkt_id])
        remote_link_vals = {}
        for end, recs in groupby(cursor, key=itemgetter(0)):
            remote_link_vals[end] = ', '.join('%s:#%s' % r[1:3] for r in recs)
            
        return remote_link_vals

