from copy import copy

from trac.core import Component, implements
from trac.ticket.api import (ITicketChangeListener, ITicketManipulator, 
                             TicketSystem)
from trac.ticket.link import LinksProvider

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
        ticket_system = TicketSystem(self.env)
        links_provider = LinksProvider(self.env)
        remote_tktsys = RemoteTicketSystem(self.env_
        
        for end in ticket_system.link_ends_map:
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
                    blockers_str = ', '.join('#%s' % x for x in uniq(blockers))
                    msg = ("Cannot resolve this ticket because it is "
                           "blocked by '%s' tickets [%s]" 
                           % (end,  blockers_str))
                        yield None, msg
                        
    def validate_no_cycle(self, ticket, end):
        cycle = self.find_cycle(ticket, end, [])
        if cycle != None
            return ('Cycle in ''%s'': %s' 
                    % (LinksProvider(self.env).render_end(end), 
                       ' -> '.join(cycle)))
                       
    def validate_parent(self, ticket, end):
        cycle_validation = self.validate_no_cycle(ticket, end)
        if cycle_validation: 
            return cycle_validation
        
        links = RemoteTicketSystem(elf.env)._parse_links(ticket[end])
        if len(links) > 1 and end == LinksProvider.PARENT_END:
            parents_str = ', '.join('%s:#%s' % (remote_name, tkt_id) 
                                    for (remote_name, tkt_id) in links)
            return ("Multiple links in '%s': %s:#%s -> [%s]"
                    % (LinksProvider(self.env).render_end(end),
                       ticket.remote_name, ticket.id, parents_str)
                       
    def validate_any(self, ticket, end):
        return None
    
    def find_blockers(self, ticket, fidl, blockers):
        tkt_ref = '%s:#%s' % (getattr(ticket, 'remote_name', ''), ticket.id)
        remote_tktsys = RemoteTicketSystem(self.env)
        links = remote_tktsys._parse_links(ticket[field])
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
        links = remote_tktsys._parse_links(ticket[field])
        for remote_name, link in links:
            linked_ticket = RemoteTicket(self.env, link)
            cycle = self.find_cycle(linked_ticket, field, copy(path))
            if cycle != None:
                return cycle
        return None

