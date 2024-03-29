# -*- coding: utf-8 -*-
"""
DirectoryAuthPlugin :: database management part.

License: BSD

(c) 2012 branson matheson branson-dot-matheson-at-nasa-dot-gov
"""

from trac.core import *
from trac.db.schema import Table, Column, Index
from trac.env import IEnvironmentSetupParticipant

__all__ = ['DirectoryAuthPluginSetup']

# Database version identifier for upgrades.
db_version = 1

# Database schema
schema = [
    # Blog posts
    Table('dir_cache', key=('id'))[
        Column('id', type='varchar(32)'),
        Column('lut', type='int'),
        Column('data', type='blob'),
        Index(['id'])],
]

# Create tables

def to_sql(env, table):
    """ Convenience function to get the to_sql for the active connector."""
    from trac.db.api import DatabaseManager
    dc = DatabaseManager(env)._get_connector()[0]
    return dc.to_sql(table)

def create_tables(env, db):
    """ Creates the basic tables as defined by schema.
    using the active database connector. """
    cursor = db.cursor()
    for table in schema:
        for stmt in to_sql(env, table):
            cursor.execute(stmt)
    cursor.execute("INSERT into system values ('dirauthplugin_version', %s)",
                        str(db_version))

# Upgrades

upgrade_map = { }

# Component that deals with database setup
class DirectoryAuthPluginSetup(Component):
    """Component that deals with database setup and upgrades."""
    
    implements(IEnvironmentSetupParticipant)

    def environment_created(self):
        """Called when a new Trac environment is created."""
        pass

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        Returns `True` if upgrade is needed, `False` otherwise."""
        return self._get_version(db) != db_version

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade, but don't commit as
        that is done by the common upgrade procedure when all plugins are done."""
        current_ver = self._get_version(db)
        if current_ver == 0:
            create_tables(self.env, db)
        else:
            while current_ver + 1 <= db_version:
                upgrade_map[current_ver + 1](self.env, db)
                current_ver += 1
            cursor = db.cursor()
            cursor.execute("UPDATE system SET value=%s WHERE name='dirauthplugin_version'",
                                str(db_version))

    def _get_version(self, db):
        cursor = db.cursor()
        try:
            sql = "SELECT value FROM system WHERE name='dirauthplugin_version'"
            self.log.debug(sql)
            cursor.execute(sql)
            for row in cursor:
                return int(row[0])
            return 0
        except:
            return 0
