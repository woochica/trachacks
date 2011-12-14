from trac.core import Component, TracError, implements
from trac.env import IEnvironmentSetupParticipant
from trac.db import Table, Column, Index
from trac.db.api import DatabaseManager


class TagModelProvider(Component):

    implements(IEnvironmentSetupParticipant)

    SCHEMA = [
        Table('tags', key = ('tagspace', 'name', 'tag'))[
              Column('tagspace'),
              Column('name'),
              Column('tag'),
              Index(['tagspace', 'name']),
              Index(['tagspace', 'tag']),]
        ]
    def __init__(self):
        # Preemptive check for rollback tolerance of read-only db connections.
        # This is required to avoid breaking `environment_needs_upgrade`,
        #   if the plugin uses intentional db transaction errors for the test.
        self.rollback_is_safe = True
        try:
            db = DatabaseManager(self.env).get_connection()
            if hasattr(db, 'readonly'):
                db = DatabaseManager(self.env).get_connection(readonly=True)
                cursor = db.cursor()
                # Test needed for rollback on read-only connections.
                cursor.execute("SELECT COUNT(*) FROM system")
                cursor.fetchone()
                try:
                    db.rollback()
                except AttributeError:
                    # Avoid rollback on read-only connections.
                    self.rollback_is_safe = False
                    return
                # Test passed.
        except TracError, e:
            # Trac too old - expect no constraints.
            return

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self._upgrade_db(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        if self._need_migration(db):
            return True
        try:
            cursor = db.cursor()
            cursor.execute("SELECT COUNT(*) FROM tags")
            cursor.fetchone()
            return False
        except Exception, e:
            self.log.error("DatabaseError: %s", e)
            if self.rollback_is_safe:
                db.rollback()
            return True

    def upgrade_environment(self, db):
        self._upgrade_db(db)

    def _need_migration(self, db):
        try:
            cursor = db.cursor()
            cursor.execute("SELECT COUNT(*) FROM wiki_namespace")
            cursor.fetchone()
            self.env.log.debug("tractags needs to migrate old data")
            return True
        except Exception, e:
            # The expected outcome for any up-to-date installation.
            if self.rollback_is_safe:
                db.rollback()
            return False

    def _upgrade_db(self, db):
        try:
            try:
                from trac.db import DatabaseManager
                db_backend, _ = DatabaseManager(self.env)._get_connector()
            except ImportError:
                db_backend = self.env.get_db_cnx()

            cursor = db.cursor()
            for table in self.SCHEMA:
                for stmt in db_backend.to_sql(table):
                    self.env.log.debug(stmt)
                    cursor.execute(stmt)
            db.commit()

            # Migrate old data
            if self._need_migration(db):
                cursor = db.cursor()
                cursor.execute("""
                    INSERT INTO tags
                            (tagspace, name, tag)
                        SELECT 'wiki', name, namespace
                        FROM    wiki_namespace
                    """)
                cursor.execute("DROP TABLE wiki_namespace")
                db.commit()
        except Exception, e:
            self.log.error("DatabaseError: %s", e)
            db.rollback()
            raise

