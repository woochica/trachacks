import re

from trac.core import Component, Interface, implements
from trac.config import IntOption
from trac.env import IEnvironmentSetupParticipant
from trac.db import DatabaseManager
from trac.resource import ResourceNotFound
from tracremoteticket import db_default

__all__ = ['RemoteTicketSystem']

class RemoteTicketSystem(Component):
    
    implements(IEnvironmentSetupParticipant, 
               #ITicketChangeListener, 
               #ITicketManipulator,
               )
    
    cache_ttl = IntOption('remoteticket', 'cache_ttl', 60000,
        """Timeout in milliseconds for cached tickets.""")
    
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
    
    # Public methods
    def get_remote_trac(self, remote_name):
        try:
            intertrac = self._intertracs[remote_name]
        except KeyError:
            raise ResourceNotFound("Remote Trac '%s' is unknown." 
                                   % remote_name,
                                   "Invalid InterTrac alias")
        return intertrac
    
    # Private methods        
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
