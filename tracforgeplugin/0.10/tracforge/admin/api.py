from trac.core import *
from trac.env import IEnvironmentSetupParticipant

import db_default

class IProjectSetupParticipant(Interface):
    """An extension-point interface for performing actions on project creation."""
    
    def get_setup_actions(self):
        """Return an iterable of names."""
        
    def get_setup_action_description(self, action):
        """Return a string description of the given action."""
        
    def execute_setup_action(self, req, proj, action, args):
        """Perform the given setup action on an environment."""
    
class IProjectChangeListener(Interface):
    """An extension-point interface for performing actions on project changes."""
    pass # TODO: Implement this
    
class TracForgeAdminSystem(Component):
    """Central stuff for tracforge.admin."""

    setup_participants = ExtensionPoint(IProjectSetupParticipant)
    
    implements(IEnvironmentSetupParticipant)
    
    # Public methods
    def get_project_setup_participants(self):
        """Return a dict of `{action: {'provider': provider, 'description': description}}`."""
        data = {}
        for provider in self.setup_participants:
            for action in provider.get_setup_actions():
                data[action] = {
                    'provider': provider,
                    'description': provider.get_setup_action_description(action),
                }
        return data

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.found_db_version = 0
        self.upgrade_environment(self.env.get_db_cnx())
        
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name=%s", (db_default.name,))
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
            cursor.execute("INSERT INTO system (name, value) VALUES (%s, %s)",(db_default.name, db_default.version))
        else:
            cursor.execute("UPDATE system SET value = %s WHERE name=%s",(db_default.name, db_default.version))
            for tbl in db_default.tables:
                try:
                    cursor.execute('DROP TABLE %s'%tbl.name,)
                except:
                    pass
            
        for tbl in db_default.tables:
            for sql in db_manager.to_sql(tbl):
                cursor.execute(sql)
