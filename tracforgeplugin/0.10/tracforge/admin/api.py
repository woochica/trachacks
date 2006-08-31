from trac.core import *
from trac.env import IEnvironmentSetupParticipant

import db_default

class IProjectSetupParticipant(Interface):
    """An extension-point interface for performing actions on project creation."""
    
    def get_project_setup_actions(self):
        """Return an iterable of (name, type), where type is one of 'create' 
        or 'configure'. All configuration actions will always take place after 
        all creation tasks."""
        
    def perform_project_setup_action(self, req, env, action):
        """Perform the given setup action on an environment."""
    
class IProjectChangeListener(Interface):
    """An extension-point interface for performing actions on project changes."""
    pass # TODO: Implement this
    
class TracForgeAdminSystem(Component):
    """Central stuff for tracforge.admin."""
    
    implements(IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.found_db_version = 0
        self.upgrade_environment(self.env.get_db_cnx())
        
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name = 'tracforge.admin'")
        value = cursor.fetchone()
        if not value:
            self.found_db_version = 0
            return True
        else:
            self.found_db_version = int(value[0])
            self.log.debug('TracforgeAdminSystem: Found db version %s, current is %s' % (self.found_db_version, db_default.version))
            return self.found_db_version < db_default.version
        
    def upgrade_environment(self, db):
        # 0.10 compatibility hack (thanks Alec)
        try:
            from trac.db import DatabaseManager
            db_manager, _ = DatabaseManager(self.env)._get_connector()
        except ImportError:
            db_manager = db
    
        # Insert the default table
        cursor = db.cursor()
        if not self.found_db_version:
            cursor.execute("INSERT INTO system (name, value) VALUES ('tracforge.admin', %s)",(db_default.version,))
        else:
            cursor.execute("UPDATE system SET value = %s WHERE name = 'tracforge.admin'",(db_default.version,))
            for tbl in db_default.tables:
                try:
                    cursor.execute('DROP TABLE %s'%tbl.name,)
                except:
                    pass
            
        for tbl in db_default.tables:
            for sql in db_manager.to_sql(tbl):
                cursor.execute(sql)
