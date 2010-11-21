# -*- coding: utf-8 -*-
import time
from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from reportmanager import CustomReportManager

class ClientsSetupParticipant(Component):
    implements(IEnvironmentSetupParticipant)
    
    db_version_key = None
    db_version = None
    db_installed_version = None
    
    def __init__(self):
        self.db_version_key = 'clients_plugin_version'
        self.db_version = 6
        self.db_installed_version = None

        # Initialise database schema version tracking.
        db = self.env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name=%s", (self.db_version_key,))
        try:
            self.db_installed_version = int(cursor.fetchone()[0])
        except:
            @self.env.with_transaction()
            def do_init(db):
                cursor = db.cursor()
                self.db_installed_version = 0
                cursor.execute("INSERT INTO system (name,value) VALUES(%s,%s)",
                               (self.db_version_key, self.db_installed_version))

    def system_needs_upgrade(self):
        return self.db_installed_version < self.db_version
    
    def do_db_upgrade(self, db):
        cursor = db.cursor()

        # Do the staged updates
        try:
            if self.db_installed_version < 2:
                print 'Creating client table'
                cursor.execute('CREATE TABLE client ('
                               'name               TEXT,'
                               'description        TEXT,'
                               'changes_list       TEXT,'
                               'changes_period     TEXT,'
                               'changes_lastupdate INTEGER,'
                               'summary_list       TEXT,'
                               'summary_period     TEXT,'
                               'summary_lastupdate INTEGER'
                               ')')
                # Import old Enums
                cursor.execute('INSERT INTO client (name) '
                               'SELECT name FROM enum WHERE type=%s', ('client',))
                # Clean them out
                cursor.execute('DELETE FROM enum WHERE type=%s', ('client',))
            
            if self.db_installed_version < 3:
               print 'Updating clients table (v3)'
               cursor.execute('ALTER TABLE client '
                              'ADD COLUMN default_rate INTEGER')
               cursor.execute('ALTER TABLE client '
                              'ADD COLUMN currency     TEXT')
            
            if self.db_installed_version < 4:
                print 'Updating clients table (v4)'
                cursor.execute('CREATE TABLE client_events ('
                               'name               TEXT,'
                               'summary            TEXT,'
                               'action             TEXT,'
                               'lastrun            INTEGER'
                               ')')
                cursor.execute('CREATE TABLE client_event_summary_options ('
                               'client_event       TEXT,'
                               'client             TEXT,'
                               'name               TEXT,'
                               'value              TEXT'
                               ')')
                cursor.execute('CREATE TABLE client_event_action_options ('
                               'client_event       TEXT,'
                               'client             TEXT,'
                               'name               TEXT,'
                               'value              TEXT'
                               ')')

            if self.db_installed_version < 5:
                print 'Updating clients table (v5)'
                # NB: Use single quotes for literals for better compat
                cursor.execute("INSERT INTO client_events "
                               "SELECT 'Weekly Summary', 'Milestone Summary', 'Send Email', MAX(summary_lastupdate) "
                               "FROM client")
                cursor.execute("INSERT INTO client_event_action_options "
                               "SELECT 'Weekly Summary', name, 'Email Addresses', summary_list "
                               "FROM client "
                               "WHERE summary_list != ''")
                cursor.execute("INSERT INTO client_events "
                               "SELECT 'Ticket Changes', 'Ticket Change Summary', 'Send Email', MAX(changes_lastupdate) "
                               "FROM client")
                cursor.execute("INSERT INTO client_event_action_options "
                               "SELECT 'Ticket Changes', name, 'Email Addresses', changes_list "
                               "FROM client "
                               "WHERE changes_list != ''")
                cursor.execute('CREATE TEMPORARY TABLE client_tmp ('
                               'name               TEXT,'
                               'description        TEXT,'
                               'default_rate       INTEGER,'
                               'currency           TEXT'
                               ')')
                cursor.execute('INSERT INTO client_tmp SELECT name, description, default_rate, currency FROM client')
                cursor.execute('DROP TABLE client')
                cursor.execute('CREATE TABLE client ('
                               'name               TEXT,'
                               'description        TEXT,'
                               'default_rate       INTEGER,'
                               'currency           TEXT'
                               ')')
                cursor.execute('INSERT INTO client SELECT name, description, default_rate, currency FROM client_tmp')
                cursor.execute('DROP TABLE client_tmp')
            
            if self.db_installed_version < 6:
                print 'Updating clients table (v6)'
                cursor.execute('CREATE TEMPORARY TABLE client_tmp ('
                               'name               TEXT,'
                               'description        TEXT,'
                               'default_rate       DECIMAL(10,2),'
                               'currency           TEXT'
                               ')')
                cursor.execute('INSERT INTO client_tmp SELECT name, description, default_rate, currency FROM client')
                cursor.execute('DROP TABLE client')
                cursor.execute('CREATE TABLE client ('
                               'name               TEXT,'
                               'description        TEXT,'
                               'default_rate       DECIMAL(10,2),'
                               'currency           TEXT'
                               ')')
                cursor.execute('INSERT INTO client SELECT name, description, default_rate, currency FROM client_tmp')
                cursor.execute('DROP TABLE client_tmp')
            
            #if self.db_installed_version < 7:
            #    print 'Updating clients table (v7)'
            #    cursor.execute('...')
            
            # Updates complete, set the version
            cursor.execute("UPDATE system SET value=%s WHERE name=%s", 
                           (self.db_version, self.db_version_key))
        except Exception, e:
            print ("WorklogPlugin Exception: %s" % (e,));
            db.rollback()

    def do_reports_upgrade(self):
        mgr = CustomReportManager(self.env, self.log)
        r = __import__('reports', globals(), locals(), ['reports'])
        
        for report_group in r.reports:
            rlist = report_group['reports']
            group_title = report_group['title']
            for report in rlist:
                title = report['title']
                new_version = report['version']
                mgr.add_report(report["title"], 'Clients Plugin', \
                               report['description'], report['sql'], \
                               report['uuid'], report['version'],
                               'Timing and Estimation Plugin',
                               group_title)

    def ticket_fields_need_upgrade(self):
        section = 'ticket-custom'
        return ('text' != self.config.get(section, 'client') \
                or 'text' != self.config.get(section, 'clientrate'))
    
    def do_ticket_field_upgrade(self):
        section = 'ticket-custom'
        
        self.config.set(section,'client', 'text')
        self.config.set(section,'client.label', 'Client')

        self.config.set(section,'clientrate', 'text')
        self.config.set(section,'clientrate.label', 'Client Charge Rate')

        self.config.save();


    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)
    
    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.

        """
        return (self.system_needs_upgrade() \
                or self.ticket_fields_need_upgrade())

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        print 'ClientsPlugin needs an upgrade'
        print ' * Upgrading db'
        @self.env.with_transaction(db)
        def real_do_db_upgrade(db):
            self.do_db_upgrade(db)
        print ' * Upgrading reports'
        self.do_reports_upgrade()

        if self.ticket_fields_need_upgrade():
            print ' * Upgrading fields'
            self.do_ticket_field_upgrade()

        print 'Done Upgrading'

