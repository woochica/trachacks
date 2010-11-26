import re

from trac.core import Component, Interface, implements, TracError
from trac.config import IntOption
from trac.env import IEnvironmentSetupParticipant
from trac.db import DatabaseManager
from trac.resource import ResourceNotFound
from trac.ticket.api import TicketSystem
from trac.util import unique

from tracremoteticket import db_default

__all__ = ['RemoteTicketSystem']

PARSE_LINKS_ERR_STRING = """Trac is parsing ticket links of the form name:#N.
Use the remote-ticket branch of Trac, or replace
  NUMBERS_RE = re.compile(r'\d+', re.U)
with
  NUMBERS_RE = re.compile(r'(?:^|[\s,])#?(\d+)', re.U)
in 'trac/ticket/api.py'."""

class RemoteTicketSystem(Component):
    
    implements(IEnvironmentSetupParticipant,
               )
    
    cache_ttl = IntOption('remoteticket', 'cache_ttl', 60000,
        """Timeout in milliseconds for cached tickets.""")
    
    # Regular expression to match remote links, a remote link is an
    # InterTrac label, a colon, an optional hash/pound, then a number
    # e.g. '1, #2, linked:#3 4 other:5,6' -> [('linked', '3'), ('other', '5')]
    REMOTES_RE = re.compile(r'(\w+):#?(\d+)', re.U)
    
    def __init__(self):
        # Check that Trac will not try to save/process the remote tickets that
        # this plugin injects
        canary = TicketSystem(self.env).parse_links('#1, remote:#2')
        if len(canary) != 1:
            raise TracError(PARSE_LINKS_ERR_STRING)
                
        self._intertracs = self._get_remotes_config()
        
    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        @self.env.with_transaction()
        def do_db_create(db):
            db_manager, _ = DatabaseManager(self.env)._get_connector()
            cursor = db.cursor()
            for table in db_default.schema:
                for sql in db_manager.to_sql(table):
                    cursor.execute(sql)       
            cursor.execute('INSERT INTO system (name, value) VALUES (%s, %s)',
                           (db_default.name, db_default.version))
        
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute('SELECT value FROM system WHERE name=%s',
                       (db_default.name,))
        value = cursor.fetchone()
        if not value:
            self.found_db_version = 0
        else:
            self.found_db_version = int(value[0])
        
        if self.found_db_version < db_default.version:
            return True
        elif self.found_db_version > db_default.version:
            raise TracError('Database newer than %s version', db_default.name)
        else:
            return False
        
    def upgrade_environment(self, db):
        if self.found_db_version == 0:
            self.environment_created()
            return
        
        cursor = db.cursor()
        for i in range(self.found_db_version+1, db_default.version+1):
            name = 'db%i' % i
            try:
                upgrades = __import__('upgrades', globals(), locals(), [name])
                script = getattr(upgrades, name)
            except AttributeError:
                raise TracError('No upgrade module for %s version %i',
                                db_default.name, i)
            script.do_upgrade(self.env, i, cursor)
            cursor.execute('UPDATE system SET value=%s WHERE name=%s',
                           (db_default.version, db_default.name))
            db.commit()
            self.log.info('Upgraded %s database version from %d to %d', 
                          db_default.name, i-1, i)
    
    # Public methods
    def get_remote_tracs(self):
        intertracs = [v for k,v in self._intertracs.items() 
                      if isinstance(v, dict) and 'url' in v]
        intertracs.sort()
        return intertracs
        
    def get_remote_trac(self, remote_name):
        try:
            intertrac = self._intertracs[remote_name]
        except KeyError:
            raise ResourceNotFound("Remote Trac '%s' is unknown." 
                                   % remote_name,
                                   "Invalid InterTrac alias")
        try:
            intertrac['url']
        except KeyError:
            raise ResourceNotFound("Remote Trac '%s' has no address configured."
                                   % remote_name, 
                                   "Invalid InterTrac alias")
        return intertrac
    
    def parse_links(self, value):
        if not value:
            return []
        return list(unique((name, int(id)) 
                           for name, id in self.REMOTES_RE.findall(value)))
        
    # Private methods        
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
