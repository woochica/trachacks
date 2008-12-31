# Trac core imports
from trac.core import *
from trac.config import *

# Trac extension point imports
from trac.env import IEnvironmentSetupParticipant

class mtSetupParticipant(Component):
    """Sets up Trac system for the Milestone Teams plugin."""
    implements(IEnvironmentSetupParticipant)

    db_version_key = None
    db_version = None
    db_installed_version = None

    def __init__(self):
        self.db_version_key = 'milestoneteams_plugin_version'
        self.db_version = 1
        self.db_installed_version = None

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name=%s", (self.db_version_key, ))
        try:
            self.db_installed_version = int(cursor.fetchone()[0])
        except:
            self.db_installed_version = 0
            cursor.execute("INSERT INTO system (name,value) VALUES(%s,%s)", (self.db_version_key, self.db_installed_version))
            db.commit()

        db.close()

    def system_needs_upgrade(self):
        return self.db_installed_version < self.db_version
    
    def do_db_upgrade(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        try:
            if self.db_installed_version < 1:
                print "Creating 'milestone_teams' table."
                cursor.execute("""CREATE TABLE milestone_teams (
                    milestone text,
                    username text,
                    role integer,
                    notify integer,
                    UNIQUE (milestone, username),
                    FOREIGN KEY (milestone) REFERENCES milestone(name),
                    FOREIGN KEY (username) REFERENCES session(sid)
                   )""")

            print "Registering plugin version."
            cursor.execute("UPDATE system SET value=%s WHERE name=%s", (self.db_version, self.db_version_key))

            db.commit()
            db.close()
        except Exception, e:
            self.log.error("MilestoneTeams Exception: %s" % (e, ))
            db.rollback()

    def environment_created(self):
        """Peform setup tasks when the environment is first created."""
        if self.environment_needs_upgrade(self, None):
            self.upgrade_environment(self)

    def environment_needs_upgrade(self, db):
        """Check to see if the current environment is up to date for our purposes."""
        return self.system_needs_upgrade()

    def upgrade_environment(self, db):
        """Make changes to environment to support our needs."""
        print 'MilestoneTeams plugin needs an upgrade'
        print ' * Upgrading db'
        self.do_db_upgrade()
        print 'Done upgrading'
