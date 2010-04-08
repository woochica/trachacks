# -*- coding: utf-8 -*-
import time
from trac.core import *
from trac.env import IEnvironmentSetupParticipant
#from reportmanager import CustomReportManager

class JobControlSetupParticipant(Component):
    implements(IEnvironmentSetupParticipant)
    
    db_version_key = None
    db_version = None
    db_installed_version = None
    
    def __init__(self):
        self.db_version_key = 'jobcontrol_plugin_version'
        self.db_version = 1
        self.db_installed_version = None

        # Initialise database schema version tracking.
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name=%s", (self.db_version_key,))
        try:
            self.db_installed_version = int(cursor.fetchone()[0])
        except:
            self.db_installed_version = 0
            cursor.execute("INSERT INTO system (name,value) VALUES(%s,%s)",
                           (self.db_version_key, self.db_installed_version))
            db.commit()
            db.close()

    def system_needs_upgrade(self):
        return self.db_installed_version < self.db_version
    
    def do_db_upgrade(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Do the staged updates
        try:
            if self.db_installed_version < 1:
                print 'Creating job table'
                cursor.execute('DROP TABLE job ')
                cursor.execute('CREATE TABLE job ('
                               'id               TEXT,'
                               'release        TEXT,'
                               'enabled       TEXT'
                               ')')
            
            # Updates complete, set the version
            cursor.execute("UPDATE system SET value=%s WHERE name=%s", 
                           (self.db_version, self.db_version_key))
            db.commit()
            db.close()
        except Exception, e:
            self.log.error("WorklogPlugin Exception: %s" % (e,));
            db.rollback()

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)
    
    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.

        """
        return self.db_installed_version < self.db_version
        return (self.system_needs_upgrade() \
                or self.ticket_fields_need_upgrade())

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        print 'JobControlPlugin needs an upgrade'
        print ' * Upgrading db'
        self.do_db_upgrade()
        """
        print ' * Upgrading reports'
        self.do_reports_upgrade()

        if self.ticket_fields_need_upgrade():
            print ' * Upgrading fields'
            self.do_ticket_field_upgrade()
        """
        print 'Done Upgrading'

