import re

from genshi.builder import Markup, tag
from genshi.filters.transform import Transformer

from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.resource import ResourceNotFound
from trac.ticket import TicketSystem
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script
from trac.web.href import Href

from tracremoteticket.api import RemoteTicketSystem
from tracremoteticket.links import RemoteLinksProvider
from tracremoteticket.model import RemoteTicket

__all__ = ['RemoteTicketModule']

class RemoteTicketModule(Component):
    implements(ITemplateProvider,
               IRequestFilter,
               ITemplateStreamFilter,
               )

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('tracremoteticket', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        # Intercept linked_val argument, if it matches the URL of a known
        # remote site then parse it and remove linked_val
        if 'linked_val' in req.args:
            linked_val = req.args['linked_val']
            patt = re.compile(r'(.+)/ticket/(\d+)')
            for name, site in RemoteTicketSystem(self.env)._intertracs.items():
                m = patt.match(linked_val)
                if m:
                    remote_base, remote_tkt_id = m.groups()
                    if remote_base == site['url'].rstrip('/'):
                        req.args['linked_remote_val'] = '%s:#%s' \
                                                        % (name, remote_tkt_id)
                        del req.args['linked_val']
                        break
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/ticket') and data:
            return self._do_ticket(req, template, data, content_type)
        elif req.path_info.startswith('/newticket') and data:
            return self._do_newticket(req, template, data, content_type)
        else:
            return (template, data, content_type)
        
    def _do_ticket(self, req, template, data, content_type):
        # Append remote linked tickets, to list of linked tickets
        if 'ticket' in data and 'linked_tickets' in data:
            ticket = data['ticket']
            RemoteLinksProvider(self.env).augment_ticket(ticket)
            data['linked_tickets'].extend(self._remote_tickets(ticket))
        
        # Provide list of remote sites if newlinked form options are present
        if 'newlinked_options' in data:
            remote_sites = RemoteTicketSystem(self.env).get_remote_tracs()
            data['remote_sites'] = remote_sites
        
        return (template, data, content_type)
        
    def _do_newticket(self, req, template, data, content_type):
        link_remote_val = req.args.get('linked_remote_val', '')
        pattern = RemoteTicketSystem(self.env).REMOTES_RE
        lrv_match = pattern.match(link_remote_val)
        link_end = req.args.get('linked_end', '')
        ends_map = TicketSystem(self.env).link_ends_map
        
        if ('ticket' in data and lrv_match and link_end in ends_map):
            ticket = data['ticket']
            remote_name = lrv_match.group(1)
            remote_id = lrv_match.group(2)
            remote_ticket = RemoteTicket(self.env, remote_name, remote_id)
            link_fields = [f for f in ticket.fields if f['name'] == link_end]
            copy_field_names = link_fields[0]['copy_fields']
            
            ticket[link_end] = link_remote_val
            for fname in copy_field_names:
                ticket[fname] = remote_ticket[fname]
            
            data['remote_ticket'] = remote_ticket
            
        return (template, data, content_type)
    
    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if 'ticket' in data and 'remote_sites' in data:
            add_script(req, 'tracremoteticket/js/remoteticket.js')
            
            transf = Transformer('//select[@id="linked-end"]')
            label = tag.label(' in ', for_='remote-site')
            local = tag.option('this project', value=req.href.newticket(),
                               selected='selected')
            remotes = [tag.option(rs['title'], 
                                  value=Href(rs['url']).newticket())
                       for rs in data['remote_sites']]
            select = tag.select([local] + remotes, id='remote-site')
            content = label + select
            stream |= transf.after(content)
            
        return stream
    
    def _remote_tickets(self, ticket):
        link_fields = [f for f in ticket.fields if f['type'] == 'link']
        rts = RemoteTicketSystem(self.env)
        
        linked_tickets = []
        linked_rejects = []
        for field in link_fields:
            for link_name, link in rts.parse_links(ticket[field['name']]):
                try:
                    tkt = RemoteTicket(self.env, link_name, link)
                    linked_tickets.append(tkt)
                except ResourceNotFound:
                    linked_rejects.append((link_name, link))
                    
        return [(field['label'], '%s:%s' % (tkt.remote_name, tkt.id), tkt)
                for tkt in linked_tickets]

