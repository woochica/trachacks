import re

from genshi.builder import Markup, tag
from genshi.filters.transform import Transformer

from pkg_resources import resource_filename

from trac.core import Component, Interface, implements
from trac.env import IEnvironmentSetupParticipant
from trac.db import DatabaseManager
from trac.ticket.api import ITicketChangeListener, ITicketManipulator
from trac.web.api import ITemplateStreamFilter, IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script
from trac.web.href import Href
from tracremoteticket import db_default
from tracremoteticket.model import RemoteTicket

__all__ = ['RemoteTicketSystem']

class RemoteTicketSystem(Component):
    
    implements(IEnvironmentSetupParticipant, 
               #ITicketChangeListener, 
               #ITicketManipulator,
               IRequestFilter,
               ITemplateProvider,
               ITemplateStreamFilter,
               )
    
    # Regular expression to match remote links, a remote link is an
    # InterTrac label, a colon, an optional hash/pound, then a number
    # e.g. '1, #2, linked:#3 4 other:5,6' -> [('linked', '3'), ('other', '5')]
    REMOTES_RE = re.compile(r'(\w+):#?(\d+)', re.U)
    
    def __init__(self):
        self._intertracs = self._get_remotes_config()
    
    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.found_db_version = 0
        self.upgrade_environment(self.env.get_db_cnx())
    
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute('SELECT value FROM system WHERE name=%s',
                       (db_default.name,))
        value = cursor.fetchone()
        if not value:
            self.found_db_version = 0
            return True
        else:
            self.found_db_version = int(value[0])
            if self.found_db_version < db_default.version:
                return True
        
        return False
        
    def upgrade_environment(self, db):
        db_manager, _ = DatabaseManager(self.env)._get_connector()
        cursor = db.cursor()
        cursor.execute('INSERT INTO system (name, value) VALUES (%s, %s)',
                       (db_default.name, db_default.version))
        for table in db_default.schema:
            for sql in db_manager.to_sql(table):
                cursor.execute(sql)
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if 'ticket' in data and 'linked_tickets' in data:
            ticket = data['ticket']
            data['linked_tickets'].extend(self._remote_tickets(ticket))
            
        if 'ticket' in data and 'newlinked_options' in data:
            data['remote_sites'] = self._remote_sites()
            
        return (template, data, content_type)
    
    def filter_stream(self, req, method, filename, stream, data):
        if 'ticket' in data and 'remote_sites' in data:
            add_script(req, 'tracremoteticket/js/remoteticket.js')
            
            transf = Transformer('//select[@id="linked-end"]')
            label = tag.label('in', for_='remote-site')
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
        
        return [(field['label'], 
                 '%s:%s' % (dest_name, dest),
                 RemoteTicket(self.env, dest_name, dest))
                for field in link_fields
                for dest_name, dest in self._parse_links(ticket[field['name']])
                          ]
    
    def _remote_sites(self):
        intertracs = [v for k,v in self._intertracs.items() 
                        if isinstance(v, dict) and 'url' in v]
        intertracs.sort()
        return intertracs
        
    def _parse_links(self, value):
        if not value:
            return []
        return [(name, int(id)) for name, id in self.REMOTES_RE.findall(value)]
        
    def _get_remotes_config(self):
        '''Return dict of intertracs and intertrac aliases.
        
        Adapted from code in trac.wiki.intertrac.InterTracDispatcher
        '''
        defin_patt = re.compile(r'(\w+)\.(\w+)')
        config = self.config['intertrac']
        intertracs = {}
        for key, val in config.options():
            m = defin_patt.match(key)
            if m:
                prefix, attribute = m.groups()
                intertrac = intertracs.setdefault(prefix, {})
                intertrac[attribute] = val
            else:
                intertracs[key] = val
        
        return intertracs
                
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('tracremoteticket', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
    
