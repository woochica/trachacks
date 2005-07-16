from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from discussion.db import version as discussion_version, schema

class DiscussionInit(Component):
    """ Initialise database and environment for discussion component """
    implements(IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant
    def environment_created(self):
        pass
    
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        # Database is up to date?
        try:
            cursor.execute("SELECT value FROM system WHERE name='discussion_version'")
            version = int(cursor.fetchone()[0])
            return version != discussion_version
        except:
            return True
        return False
    
    def upgrade_environment(self, db):
        cursor = db.cursor()
        # Initial table creation
        try:
            for table in schema:
                cursor.execute(db.to_sql(table))
            cursor.execute("INSERT INTO system VALUES ('discussion_version', %i)", discussion_version)
        except:
            # Upgrade
            # TODO Table upgrades...
            cursor.execute("UPDATE system SET value = %i WHERE name = 'discussion_version'", discussion_version)
        db.commit()
