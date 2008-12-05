# -*- coding: utf-8 -*-
"""
TracPastePlugin: code to manage database setup and upgrades
"""

import inspect, textwrap
from trac.core import *
from trac.db import Table, Column
from trac.env import IEnvironmentSetupParticipant

__all__ = ['TracpasteSetup']

schema_version = 2

class TracpasteSetup(Component):
    implements(IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant
    def environment_created(self):
        """ Called when a new environment is created. Procedure is similar to
        an environment upgrade, but we also need to commit the changes
        ourselves. """
        db = self.env.get_db_cnx()
        self.upgrade_environment(db)
        db.commit()

    def environment_needs_upgrade(self, db):
        """ Determine if an environment upgrade is required. """
        current_version = self._get_version(db)
        self.env.log.debug("current=%d schema=%d",
                           current_version, schema_version)
        return current_version < schema_version

    def upgrade_environment(self, db):
        """ Upgrade our part of the database to the latest version. Note that
        we don't commit the changes here, as this is done by the common upgrade
        procedure instead. """
        current_version = self._get_version(db)
        for version in range(current_version + 1, schema_version + 1):
            self.env.log.debug("version=%d", version)
            for function in version_map.get(version, []):
                self.env.log.debug("function=%s", function)
                self.log.info(textwrap.fill(inspect.getdoc(function)))
                function(self.env, db)
                self.log.info('Done.')

        """ Reget version, since it may have changed during the update
        update procedure above (when upgrading from v1 to v2) """
        current_version = self._get_version(db)
        cursor = db.cursor()
        try:
            if current_version == 0:
                cursor.execute("INSERT INTO system VALUES "
                               "('tracpaste_version',%s)", (schema_version,))
                self.log.info('Created TracPastePlugin tables')
            else:
                cursor.execute("UPDATE system SET value=%s WHERE "
                               "name='tracpaste_version'", (schema_version,))
                self.log.info('Upgraded TracPastePlugin tables from '
                              ' version %d to %d', current_version, schema_version)
            db.commit()
        except Exception, e:
            db.rollback()
            self.env.log.error(e, exc_info=1)
            raise TracError(str(e))

    # private methods
    def _get_version(self, db):
        """ Determine the version of the database scheme for this plugin
        that is currently used. Some extra work is required, since early
        versions of the plugin didn't add tracpaste_version to the
        system table. """
        cursor = db.cursor()

        stmt = "SELECT value FROM system WHERE name='tracpaste_version'"
        try:
            self.log.debug(stmt)
            cursor.execute(stmt)
            row = cursor.fetchone()
            if row:
                return int(row[0])
        except:
            db.rollback()

        stmt = "SELECT count(*) FROM pastes"
        try:
            self.env.log.debug(stmt)
            cursor.execute(stmt)
            row = cursor.fetchone()
            return row and 1 or 0
        except:
            db.rollback()
            return 0

        return 0


# Helpers
def _to_sql(env, db, table):
    from trac.db import DatabaseManager
    connector, _ = DatabaseManager(env)._get_connector()
    return connector.to_sql(table)

# Update procedures
def add_paste_table(env, db):
    """ Add a table for storing pastes."""
    table = Table('pastes', key='id')[
        Column('id', auto_increment=True),
        Column('title'),
        Column('author'),
        Column('mimetype'),
        Column('data'),
        Column('time', type='int')
    ]

    cursor = db.cursor()
    try:
        for stmt in _to_sql(env, db, table):
            env.log.debug(stmt)
            cursor.execute(stmt)
    except Exception, e:
        db.rollback()
        env.log.error(e, exc_info=1)
        raise TracError(str(e))

def add_database_version(env, db):
    """ Add tracpaste_version to system table. """
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO system VALUES "
                       "('tracpaste_version',%s)", (schema_version,))
    except Exception, e:
        db.rollback()
        env.log.error(e, exc_info=1)
        raise TracError(str(e))


version_map = {
    1: [add_paste_table],
    2: [add_database_version],
}
