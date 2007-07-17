# MTP_EnvironmentSetupParticipant

from trac.core import *
from trac.env import IEnvironmentSetupParticipant

"""
Extension point interface for components that need to participate in the
creation and upgrading of Trac environments, for example to create
additional database tables."""
class MTP_EnvironmentSetupParticipant(Component):
    implements(IEnvironmentSetupParticipant)

    """
    Called when a new Trac environment is created."""
    def environment_created():
        self.db_version_key = 'ManualTestingPlugin_database_version'
        self.db_version_value = 1
        self.db_installed_version_value = 0

        # Initialise database schema version tracking.
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name=%s", (self.db_version_key,))
        try:
            self.db_installed_version_value = int( cursor.fetchone()[0] )
        except:
            self.db_installed_version_value = 0
            cursor.execute("INSERT INTO system (name,value) VALUES(%s,%s)", (self.db_version_key, self.db_version_value) )
            db.commit()
            db.close()
        print "ManualTestingPlugin database version initialized."


    """
    Called when Trac checks whether the environment needs to be upgraded.
    Should return `True` if this participant needs an upgrade to be
    performed, `False` otherwise."""
    def environment_needs_upgrade(db):
        needsUpgrade = (self.db_installed_version_value < self.db_version_value)
        print "ManualTestingPlugin needs upgrade: %s", needsUpgrade
        return needsUpgrade


    """
    Actually perform an environment upgrade.
    Implementations of this method should not commit any database
    transactions. This is done implicitly after all participants have
    performed the upgrades they need without an error being raised."""
    def upgrade_environment(db):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sqlStatement = """
            CREATE TABLE mtp_suites (
                id INTEGER
                title TEXT
                description TEXT
                component TEXT
                deleted INTEGER
                user TEXT
            );
            CREATE TABLE mtp_suite_runs (
                id INTEGER
                rDate INTEGER
                status INTEGER
                version TEXT
                suite_id INTEGER
                user TEXT
            );
            CREATE TABLE mtp_plans (
                id INTEGER
                suite_id INTEGER
                cDate INTEGER
                mDate INTEGER
                title TEXT
                description TEXT
                priority TEXT
                user TEXT
            );
            CREATE TABLE mtp_plan_runs (
                id INTEGER
                plan_id INTEGER
                rDate INTEGER
                status INTEGER
                version TEXT
                ticket INTEGER
                user TEXT
            );
        """
        cursor.execute(sqlStatement)
        db.commit()
        db.close()