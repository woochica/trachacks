from trac.core import *
from trac.db import *
from trac.env import IEnvironmentSetupParticipant
from tracdiscussion.db import version as discussion_version, schema

class DiscussionInit(Component):
    """ Initialise database and environment for discussion component """
    implements(IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipanttr
    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        # Database is up to date?
        try:
            cursor.execute("SELECT value FROM system WHERE name='discussion_version'")
            for row in cursor:
                return int(row[0]) != discussion_version
            return True
        except:
            return True
        return False

    def upgrade_environment(self, db):
        cursor = db.cursor()
        # Initial table creation
        #try:
        for table in schema:
            queries = db.to_sql(table)
            for query in queries:
                cursor.execute(query)
        cursor.execute("INSERT INTO system VALUES ('discussion_version', %s)",
          [discussion_version])
        #except:
          #cursor.execute("UPDATE system SET value = %i WHERE name = 'discussion_version'", discussion_version)
