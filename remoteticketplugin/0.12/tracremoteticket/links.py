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
from trac.util.datefmt import from_utimestamp, to_utimestamp

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
        
        # We go behind trac's back to augment the ticket with remote links
        # As a result trac doesn't provide a correct old_values so fetch
        # our own
        orig_old_vals = old_values
        if old_values is None:
            old_values = {}
        else:
            self._augment_values(ticket.id, old_values)
        
        @self.env.with_transaction()
        def do_changed(db):
            cursor = db.cursor()
            for end in link_fields:
                # Determine links added or removed in this change by taking the
                # set difference of new and old values
                new_rtkts = set(remote_tktsys.parse_links(ticket[end]))
                old_rtkts = set(remote_tktsys.parse_links(old_values.get(end)))
                
                links_added = new_rtkts - old_rtkts
                links_removed = old_rtkts - new_rtkts
                links_changed = old_rtkts ^ new_rtkts # Additons and removals
                
                other_end = ticket_system.link_ends_map[end]
                
                # Add link records for remote links created in this change
                records = [('', ticket.id, end, rname, rid)
                           for rname, rid in links_added]
                if other_end:
                    records += [(rname, rid, other_end, '', ticket.id)
                                for rname, rid in links_added]
                cursor.executemany('''
                    INSERT INTO remote_ticket_links
                    (source_name, source, type, destination_name, destination)
                    VALUES (%s, %s, %s, %s, %s)''', 
                    records)
                
                # Remove link records for remote links removed in this change
                records = [('', ticket.id, end, rname, rid)
                           for rname, rid in links_removed]
                if other_end:
                    records += [(rname, rid, other_end, '', ticket.id)
                                for rname, rid in links_added]
                cursor.executemany('''
                    DELETE FROM remote_ticket_links 
                    WHERE source_name=%s AND source=%s AND type=%s
                    AND destination_name=%s AND destination=%s''', 
                    records)
                
                # Record change history in ticket_change
                # Again we're going behind trac's back, so take care not to
                # obliterate existing records:
                #  - If the field (end) has changed local links, as well as
                #    changed remote links then update the record
                #  - If the only change was to remote links then there is no
                #    ticket_change record to update, so insert one
                if links_changed and orig_old_vals is not None:
                    when_ts = to_utimestamp(ticket['changetime'])
                    
                    cursor.execute('''
                        UPDATE ticket_change
                        SET oldvalue=%s, newvalue=%s
                        WHERE ticket=%s AND time=%s AND author=%s AND field=%s
                        ''',
                        (old_values[end], ticket[end], 
                         ticket.id, when_ts, author, end))
                    
                    # Check that a row was updated, if so
                    if cursor.rowcount >= 1:
                        continue
                    
                    cursor.execute('''
                        INSERT INTO ticket_change
                        (ticket, time, author, field, oldvalue, newvalue)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ''',
                        (ticket.id, when_ts, author, end,
                         old_values[end], ticket[end]))

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
                    blockers_str = ', '.join('%s:#%s' % rlink
                                             for rlink in unique(blockers))
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
        remote_tktsys = RemoteTicketSystem(self.env)
        links = remote_tktsys.parse_links(ticket[field])
        for remote_name, link in links:
            linked_ticket = RemoteTicket(self.env, remote_name, link)
            if linked_ticket['status'] != 'closed':
                blockers.append((remote_name, link))
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
        '''Fetch remote links from the database, append them to the link fields.
        ''' 
        self._augment_values(ticket.id, ticket)
    
    def _augment_values(self, tkt_id, values):
        remote_link_vals = self._fetch_remote_links(tkt_id)
        for end, remote_links in remote_link_vals.items():
            # values is either a ticket object, or the old_values dictionary
            # Can't use .get() or 'end in  values' on ticket and old_values
            # won't contain all ends, so use try except instead
            try:
                val = values[end]
            except KeyError:
                val = ''
            if val and remote_links:
                values[end] = '%s, %s' % (val, remote_links)
            elif remote_links:
                values[end] = remote_links
    
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

