# codereviewinit.py

from trac.core import Component, implements
from trac.env import IEnvironmentSetupParticipant

from codereview.db import schema, version as codereview_version


class CodeReviewInit(Component):
    implements(IEnvironmentSetupParticipant)

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("SELECT value FROM system " \
                           "WHERE name='codereview_version'")
            version = int(cursor.fetchone()[0])
            return version != codereview_version
        except:
            return True
        return False

    def upgrade_environment(self, db):
        cursor = db.cursor()
        # This is a hack to be compatible with Trac 0.9 and 0.10
        # Maybe we will remove it, because we will juse support trac 0.10
        # after upgrade our trac
        try:
            from trac.db  import DatabaseManager
            db_manager, _ = DatabaseManager(self.env)._get_connector()
        except ImportError:
            db_manager = db
        for table in schema:
            for stmt in db_manager.to_sql(table):
                cursor.execute(stmt)
        cursor.execute("CREATE VIEW review_current AS " \
                       "SELECT id, max(version) AS version " \
                       "FROM codereview GROUP BY id ORDER BY id")
        cursor.execute("INSERT INTO system VALUES('codereview_version',%s)",
                           (codereview_version, ))
