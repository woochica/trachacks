# -*- coding: utf-8 -*-

from trac.core import *
from trac.db import Column, DatabaseManager, Index, Table
from trac.env import IEnvironmentSetupParticipant

from api import custom_fields
from tracsqlhelper import *


class SetupTracHours(Component):

    implements(IEnvironmentSetupParticipant)

    ### methods for IEnvironmentSetupParticipant

    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.
        """
        version = self.version()
        return version < len(self.steps)

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        if not self.environment_needs_upgrade(db):
            return

        version = self.version()
        for version in range(self.version(), len(self.steps)):
            for step in self.steps[version]:
                step(self)
        execute_non_query(self.env, "update system set value='%s' where name='trachours.db_version';" % len(self.steps))


    ### helper methods

    def version(self):
        """returns version of the database (an int)"""
        version = get_scalar(self.env, "select value from system where name = 'trachours.db_version';")
        if version:
            return int(version)
        return 0


    ### upgrade steps

    def create_db(self):
        ticket_time_table = Table('ticket_time', key=('id'))[
            Column('id', auto_increment=True),
            Column('ticket', type='int'),
            Column('time_submitted', type='int'),
            Column('worker'),
            Column('submitter'),
            Column('time_started', type='int'),
            Column('seconds_worked', type='int'),
            Column('comments'),
            Index(['ticket']),
            Index(['worker']),
            Index(['time_started'])]

        create_table(self.env, ticket_time_table)
        execute_non_query(self.env, "insert into system (name, value) values ('trachours.db_version', '1');")

    def update_custom_fields(self):
        ticket_custom = 'ticket-custom'
        for name in custom_fields:
            field = custom_fields[name].copy() 
            field_type = field.pop('type', 'text')
            if not self.config.get(ticket_custom, field_type):
                self.config.set(ticket_custom, name, field_type)
            for key, value in field.items():
                self.config.set(ticket_custom, '%s.%s' % (name, key), value)
        self.config.save()

    def add_query_table(self):
        time_query_table = Table('ticket_time_query', key=('id'))[
            Column('id', auto_increment=True),
            Column('title'),
            Column('description'),
            Column('query')]

        create_table(self.env, time_query_table)

    def initialize_old_tickets(self):
        execute_non_query(self.env, """
            INSERT INTO ticket_custom (ticket, name, value)
            SELECT id, 'totalhours', '0' FROM ticket WHERE id NOT IN (
            SELECT ticket from ticket_custom WHERE name='totalhours');""")

    # ordered steps for upgrading
    steps = [ [ create_db, update_custom_fields ], # version 1
              [ add_query_table ], # version 2
              [ initialize_old_tickets ], # version 3
            ]
