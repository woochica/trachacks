# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Bart Ogryczak
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import *
from trac.db.schema import Table, Column
from trac.env import IEnvironmentSetupParticipant

# Database version identifier for upgrades
db_version = 1

# Database schema
SCHEMA = [
    # Backlogs
    Table('backlog', key=('id'))[
        Column('id', type='int', auto_increment=True),
        Column('name'),
        Column('owner'),
        Column('description')],
    #Tickets in backlogs
    Table('backlog_ticket', key=('bklg_id', 'tkt_id'))[
        Column('bklg_id', type='int'),
        Column('tkt_id', type='int'),
        Column('tkt_order', type='int')],
]

# Hard-coded backlogs, which will be replaced by an Admin panel
BACKLOGS =  [(1, 'Product and Community'),
             (2, 'Sales and Business Intelligence'),
             (3, 'Business Development'),
             (4, 'System Engineering')]

def to_sql(env, table):
    """ Convenience function to get the to_sql for the active connector."""
    from trac.db.api import DatabaseManager
    dc = DatabaseManager(env)._get_connector()[0]
    return dc.to_sql(table)

def create_ordering_table(db):
    cursor = db.cursor()
    try:
        cursor.execute("SELECT count(*) FROM backlog_ticket")
    except:
        cursor.execute("""
            CREATE TABLE backlog_ticket (bklg_id INTEGER NOT NULL,
              tkt_id INTEGER NOT NULL, tkt_order REAL,
            PRIMARY KEY(bklg_id, tkt_id))""")

def create_tables(env, db):
    """ Creates the basic tables as defined by SCHEMA.
    using the active database connector. """
    cursor = db.cursor()
    for table in SCHEMA:
        for stmt in to_sql(env, table):
            cursor.execute(stmt)    
    cursor.executemany('INSERT INTO backlog (id, name) VALUES (%s, %s)', BACKLOGS)
    cursor.execute("INSERT into system values ('backlog_version', %s)", (db_version,))

def add_custom_fields(env):
    config = env.config
    config.set('ticket-custom', 'backlog', 'select')
    config.set('ticket-custom', 'backlog.label', 'Backlog')
    config.set('ticket-custom', 'backlog.options', '|'.join([b[1] for b in BACKLOGS]))
    config.set('ticket-custom', 'hard_deadline1', 'text')
    config.set('ticket-custom', 'hard_deadline1.label', 'Hard deadline')
    config.set('ticket-custom', 'hard_deadline2', 'text')
    config.set('ticket-custom', 'hard_deadline2.label', 'Reason for deadline')
    config.save()

# Upgrades

pass

# Component that deals with database setup

class BacklogSetup(Component):
    """Component that deals with database setup and upgrades."""
    
    implements(IEnvironmentSetupParticipant)

    def environment_created(self):
        """Called when a new Trac environment is created."""
        pass

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        Returns `True` if upgrade is needed, `False` otherwise."""
        return self._get_version(db) < db_version

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade, but don't commit as
        that is done by the common upgrade procedure when all plugins are done."""
        if self._get_version(db) == 0:
           create_tables(self.env, db)
           add_custom_fields(self.env)
        else:
            # do upgrades here when they are needed
            pass

    def _get_version(self, db):
        cursor = db.cursor()
        try:
            sql = "SELECT value FROM system WHERE name='backlog_version'"
            self.log.debug(sql)
            cursor.execute(sql)
            for row in cursor:
                return int(row[0])
            return 0
        except:
            return 0
