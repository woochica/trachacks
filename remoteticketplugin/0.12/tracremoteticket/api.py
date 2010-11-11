from trac.core import Component, Interface, implements
from trac.env import IEnvironmentSetupParticipant
from trac.db import DatabaseManager
from trac.ticket.api import ITicketChangeListener, ITicketManipulator

from tracremoteticket import db_default

__all__ = ['RemoteTicketSystem']

class RemoteTicketSystem(Component):
    
    implements(IEnvironmentSetupParticipant, 
               #ITicketChangeListener, 
               #ITicketManipulator,
               )
    
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
        if not self.found_db_version:
            cursor.execute('INSERT INTO system (name, value) VALUES (%s, %s)',
                           (db_default.name, db_default.version))
            for table in db_default.schema:
                for sql in db_manager.to_sql(table):
                    cursor.execute(sql)
    
    
