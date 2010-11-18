import re

from genshi.builder import Markup, tag
from genshi.filters.transform import Transformer

from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.ticket import TicketSystem
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script
from trac.web.href import Href

from tracremoteticket.api import RemoteTicketSystem
from tracremoteticket.model import RemoteTicket

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
        if data and 'ticket' in data and 'linked_tickets' in data:
            ticket = data['ticket']
            data['linked_tickets'].extend(self._remote_tickets(ticket))
            
        if data and 'ticket' in data and 'newlinked_options' in data:
            data['remote_sites'] = self._remote_sites()
        
        if data and 'ticket' in data and 'linked_end' in req.args \
                                     and 'linked_remote_val' in req.args:
            ticket = data['ticket']
            link_end = req.args['linked_end']
            lrv_patt = RemoteTicketSystem(self.env).REMOTES_RE
            lrv_match = lrv_patt.match(req.args['linked_remote_val'])
            
            if lrv_match and link_end in TicketSystem(self.env).link_ends_map:
                remote_name, remote_id = lrv_match.groups()
                remote_ticket = RemoteTicket(self.env, remote_name, remote_id)
                link_field = [f for f in ticket.fields 
                                if f['name'] == link_end][0]
                copy_field_names = link_field['copy_fields']
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
        
        return [(field['label'], 
                 '%s:%s' % (dest_name, dest),
                 RemoteTicket(self.env, dest_name, dest))
                for field in link_fields
                for dest_name, dest in rts._parse_links(ticket[field['name']])
                          ]
    
    def _remote_sites(self):
        rts = RemoteTicketSystem(self.env)
        intertracs = [v for k,v in rts._intertracs.items() 
                        if isinstance(v, dict) and 'url' in v]
        intertracs.sort()
        return intertracs

