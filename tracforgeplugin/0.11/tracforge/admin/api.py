from trac.core import *
from trac.env import IEnvironmentSetupParticipant, open_environment

import db_default

class IProjectSetupParticipant(Interface):
    """An extension-point interface for performing actions on project creation."""

    def get_setup_actions():
        """Return an iterable of names."""

    def get_setup_action_info(action):
        """Return a dict with zero or more of the following keys:
        
        description
          A string description for the step.
        
        depends
          A list of data keys step uses.
        
        optional_depends
          A list of data keys step could use.
        
        provides
          A list of data keys step creates.
        """

    def get_setup_action_default(action, env):
        """Return a string corresponding to the default argument for a given step,
        or None if the step shouldn't be included.
        """

    def execute_setup_action(action, args, data, log_cb):
        """Perform the given setup action on an environment."""
    
    def undo_setup_action(action, args, data, log_cb):
        """Reverse the given setup action."""
    
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
                data[action] = provider.get_setup_action_info(action)
                data[action]['provider'] = provider
        return data
    
    def get_projects(self, db=None):
        """Return an iterable of (shotname, env) for all known projects."""
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT name, env_path FROM tracforge_projects')
        for name, path in cursor:
            env = open_environment(path, use_cache=True)
            yield name, env

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
        old_data = {} # {table_name: (col_names, [row, ...]), ...}
        cursor = db.cursor()
        if not self.found_db_version:
            cursor.execute("INSERT INTO system (name, value) VALUES (%s, %s)",(db_default.name, db_default.version))
        else:
            cursor.execute("UPDATE system SET value=%s WHERE name=%s",(db_default.version, db_default.name))
            for tbl in db_default.tables:
                try:
                    cursor.execute('SELECT * FROM %s'%tbl.name)
                    old_data[tbl.name] = ([d[0] for d in cursor.description], cursor.fetchall())
                    cursor.execute('DROP TABLE %s'%tbl.name)
                except Exception, e:
                    if 'OperationalError' not in e.__class__.__name__:
                        raise e # If it is an OperationalError, just move on to the next table
                        
            
        for vers, migration in db_default.migrations:
            if self.found_db_version in vers:
                self.log.info('TracForgeAdminModule: Running migration %s', migration.__doc__)
                migration(old_data)

        for tbl in db_default.tables:
            for sql in db_manager.to_sql(tbl):
                cursor.execute(sql)
                
            # Try to reinsert any old data
            if tbl.name in old_data:
                data = old_data[tbl.name]
                sql = 'INSERT INTO %s (%s) VALUES (%s)' % \
                      (tbl.name, ','.join(data[0]), ','.join(['%s'] * len(data[0])))
                for row in data[1]:
                    try:
                        cursor.execute(sql, row)
                    except Exception, e:
                        if 'OperationalError' not in e.__class__.__name__:
                            raise
                        else:
                            self.log.debug('TracForgeAdminModule: Masking exception %s', e)
