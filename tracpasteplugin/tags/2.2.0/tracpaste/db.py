# -*- coding: utf-8 -*-
"""
TracPastePlugin: code to manage database setup and upgrades
"""

import inspect, textwrap
from trac.core import *
from trac.db import Table, Column, Index
from trac.env import IEnvironmentSetupParticipant

__all__ = ['TracpasteSetup']

schema_version = 3

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
        old_perms = self._has_old_permission(db)
        self.env.log.debug("old_perms=%s", old_perms)

        current_version = self._get_version(db)
        self.env.log.debug("current=%d schema=%d",
                           current_version, schema_version)

        return old_perms or (current_version < schema_version)

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
                              ' version %d to %d',
                              current_version, schema_version)
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

    def _has_old_permission(self, db):
        """ Determine whether the old PASTEBIN_USE permission is assigned
        to any subject. """
        cursor = db.cursor()

        stmt = "SELECT count(*) FROM permission WHERE action='PASTEBIN_USE'"
        try:
            self.env.log.debug(stmt)
            cursor.execute(stmt)
            row = cursor.fetchone()
            return row[0] > 0
        except:
            db.rollback()
            return False

        return False


# Helpers
def _to_sql(env, table):
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
        for stmt in _to_sql(env, table):
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

def convert_use_permissions(env, db):
    """ Convert permission PASTEBIN_USE to PASTEBIN_VIEW and PASTEBIN_CREATE. """
    # XXX: This should probably be handled using PermissionSystem instead
    cursor = db.cursor()
    try:
        cursor.execute("SELECT username FROM permission "
                       "WHERE action='PASTEBIN_USE'")
        users = []
        for row in cursor:
            users.append(row[0])
        for user in users:
            cursor.execute("INSERT INTO permission (username, action) "
                               "VALUES (%s, 'PASTEBIN_VIEW')", (user,))
            cursor.execute("INSERT INTO permission (username, action) "
                               "VALUES (%s, 'PASTEBIN_CREATE')", (user,))
            cursor.execute("DELETE FROM permission WHERE "
                           "username=%s AND action='PASTEBIN_USE'", (user,))
            env.log.debug("Pastebin permissions converted for %s ", user)
    except Exception, e:
        db.rollback()
        env.log.error(e, exc_info=1)
        raise TracError(str(e))


def add_indexes(env, db):
    """ Add indexes on fields id and time. """
    table = Table('pastes', key='id')[
        Column('id', auto_increment=True),
        Column('title'),
        Column('author'),
        Column('mimetype'),
        Column('data'),
        Column('time', type='int'),
        Index(['id',]),
        Index(['time',])
    ]

    cursor = db.cursor()
    try:
        cursor.execute("CREATE TEMPORARY TABLE pastes_old AS "
                       "SELECT * FROM pastes")
        cursor.execute("DROP TABLE pastes")

        for stmt in _to_sql(env, table):
            env.log.debug(stmt)
            cursor.execute(stmt)

        cursor.execute("INSERT INTO pastes (id,title,author,mimetype,data,time) "
                       "SELECT id,title,author,mimetype,data,time "
                       "FROM pastes_old")
        cursor.execute("DROP TABLE pastes_old")
    except Exception, e:
        db.rollback()
        env.log.error(e, exc_info=1)
        raise TracError(str(e))


version_map = {
    1: [add_paste_table],
    2: [add_database_version],
    3: [convert_use_permissions, add_indexes],
}

