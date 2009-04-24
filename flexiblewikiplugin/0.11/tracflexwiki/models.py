# -*- coding: utf-8 -*-

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.db import Table, Column, Index

class StructModelProvider(Component):
    implements(IEnvironmentSetupParticipant)

    schema = [
        Table('flex', key = ('name', ))[
            Column('name'),
            Column('parent'),
            Column('title'),
            Column('weight', type='int'),
            Column('hidden', type='int'),
            Index(['parent']),
            Index(['weight']),]
        ]

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self._upgrade_db(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("SELECT count(*) FROM flex")
            return False
        except:
            db.rollback()
            return True

    def upgrade_environment(self, db):
        self._upgrade_db(db)

    def _need_migration(self, db):
        return False

    def _upgrade_db(self, db):
        cursor = db.cursor()
        try:
            from trac.db import DatabaseManager
            db_backend, _ = DatabaseManager(self.env)._get_connector()
            for table in self.schema:
                for stmt in db_backend.to_sql(table):
                    print stmt
                    cursor.execute(stmt)
            db.commit()
        except:
            db.rollback()