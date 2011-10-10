# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Christopher Paredes
#

# SimpleMultiProject.SMP_EnvironmentSetupParticipant

from trac.core import *
from trac.db import *
from trac.env import IEnvironmentSetupParticipant
from trac.db import Table, Column, DatabaseManager


# Database schema variables
db_version_key = 'simplemultiproject_version'
db_version = 1

tables = [
    Table('smp_project', key = 'id') [
        Column('id_project', type = 'integer', auto_increment = True),
        Column('name',type = 'varchar'),
        Column('description',type='varchar')
    ],
    Table('smp_milestone_project',key = 'id') [
        Column('id', type = 'integer', auto_increment = True),
        Column('milestone',type = 'varchar'),
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
            sqlGetInstalledVersion = "SELECT value FROM system WHERE name = '%s'" % db_version_key
            cursor.execute(sqlGetInstalledVersion)
            db_installed_version = int(cursor.fetchone()[0])
        except:
            # No version currently, inserting new one.
            sqlInsertVersion = "INSERT INTO system (name, value) VALUES ('%s','%s')" % (db_version_key, db_version)
            cursor.execute(sqlInsertVersion)
        print "SimpleMultiProject database schema version: %s initialized." % db_version
        # return boolean for if we need to update or not
        needsUpgrade = (db_installed_version < db_version)
        print "SimpleMultiProject database schema is out of date: %s" % needsUpgrade
        return needsUpgrade


    """
    Actually perform an environment upgrade.
    Implementations of this method should not commit any database
    transactions. This is done implicitly after all participants have
    performed the upgrades they need without an error being raised."""
    def upgrade_environment(self, db):
        print "Upgrading SimpleMultiProject database schema"
        cursor = db.cursor()

        db_connector, _ = DatabaseManager(self.env)._get_connector()

        # Create tables
        for table in tables:
            for statement in db_connector.to_sql(table):
                cursor.execute(statement)