# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Christopher Paredes
#

# SimpleMultiProject.SMP_EnvironmentSetupParticipant

from trac.core import *
from trac.db import *
from trac.env import IEnvironmentSetupParticipant
from trac.db import Table, Column, DatabaseManager
from trac.util.text import printout


# Database schema variables
db_version_key = 'simplemultiproject_version'
db_version = 4

tables = [
    Table('smp_project', key = 'id_project') [
        Column('id_project', type = 'integer', auto_increment = True),
        Column('name',type = 'varchar(255)'),
        Column('description',type='varchar(255)')
    ],
    Table('smp_milestone_project',key = 'id') [
        Column('id', type = 'integer', auto_increment = True),
        Column('milestone',type = 'varchar(255)'),
        Column('id_project',type = 'integer')
    ],
]

tables_v2 = [
    # Added with version 2
    Table('smp_version_project',key = 'id') [
        Column('id', type = 'integer', auto_increment = True),
        Column('version',type = 'varchar(255)'),
        Column('id_project',type = 'integer')
    ],
]

tables_v3 = [
    # Added with version 3
    Table('smp_component_project',key = 'id') [
        Column('id', type = 'integer', auto_increment = True),
        Column('component',type = 'varchar(255)'),
        Column('id_project',type = 'integer')
    ],
]

"""
Extension point interface for components that need to participate in the
creation and upgrading of Trac environments, for example to create
additional database tables."""
class smpEnvironmentSetupParticipant(Component):
    implements(IEnvironmentSetupParticipant)

    """
    Called when a new Trac environment is created."""
    def environment_created(self):
        pass

    """
    Called when Trac checks whether the environment needs to be upgraded.
    Should return `True` if this participant needs an upgrade to be
    performed, `False` otherwise."""
    def environment_needs_upgrade(self, db):
        # Initialise database schema version tracking.
        cursor = db.cursor()
        # Get currently installed database schema version
        db_installed_version = 0
        try:
            sqlGetInstalledVersion = """SELECT value FROM system WHERE name = %s"""
            cursor.execute(sqlGetInstalledVersion, [db_version_key])
            db_installed_version = int(cursor.fetchone()[0])
        except:
            # No version currently, inserting new one.
            db_installed_version = 0

        self.log.debug("SimpleMultiProject database schema version: %s (should be %s)",
                       db_installed_version, db_version)
        # return boolean for if we need to update or not
        needsUpgrade = (db_installed_version < db_version)
        if needsUpgrade:
            self.log.info("SimpleMultiProject database schema version is %s, should be %s",
                          db_installed_version, db_version)
        return needsUpgrade


    """
    Actually perform an environment upgrade.
    Implementations of this method should not commit any database
    transactions. This is done implicitly after all participants have
    performed the upgrades they need without an error being raised."""
    def upgrade_environment(self, db):
        printout("Upgrading SimpleMultiProject database schema")
        cursor = db.cursor()

        db_installed_version = 0
        sqlGetInstalledVersion = """SELECT value FROM system WHERE name = %s"""
        cursor.execute(sqlGetInstalledVersion, [db_version_key])
        for row in cursor:
            db_installed_version = int(row[0])
        printout("SimpleMultiProject database schema version is %s, should be %s" %
                 (db_installed_version, db_version))

        db_connector, _ = DatabaseManager(self.env)._get_connector()

        if db_installed_version < 1:
            # Create tables
            for table in tables:
                for statement in db_connector.to_sql(table):
                    cursor.execute(statement)
                    
            sqlInsertVersion = """INSERT INTO system (name, value) VALUES (%s,%s)"""
            cursor.execute(sqlInsertVersion, [db_version_key, db_version])
            db_installed_version = 1
            
        if db_installed_version < 2:
            # Create tables
            for table in tables_v2:
                for statement in db_connector.to_sql(table):
                    cursor.execute(statement)
                    
            sqlInsertVersion = """UPDATE system SET value=%s WHERE name=%s"""
            cursor.execute(sqlInsertVersion, [db_version, db_version_key])
            db_installed_version = 2

        if db_installed_version < 3:
            # Create tables
            for table in tables_v3:
                for statement in db_connector.to_sql(table):
                    cursor.execute(statement)
                    
            sqlInsertVersion = """UPDATE system SET value=%s WHERE name=%s"""
            cursor.execute(sqlInsertVersion, [db_version, db_version_key])
            db_installed_version = 3

        if db_installed_version < 4:
            # Insert new column
            cursor.execute("""ALTER TABLE smp_project ADD summary varchar(255)""")
            
            sqlInsertVersion = """UPDATE system SET value=%s WHERE name=%s"""
            cursor.execute(sqlInsertVersion, [db_version, db_version_key])
            db_installed_version = 4
