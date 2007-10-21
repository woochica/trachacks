from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from reportmanager import CustomReportManager

class ClientsSetupParticipant(Component):
    implements(IEnvironmentSetupParticipant)
    
    version = 1
    installed_version = 0
    name = "clients_plugin_version"

    def __init__(self):
        # Initialise database schema version tracking.
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT value FROM system WHERE name=%s',
                       (self.name,))
        try:
            self.installed_version = int(cursor.fetchone()[0])
        except:
            self.installed_version = 0
            cursor.execute('INSERT INTO system (name,value) VALUES(%s,%s)',
                           (self.name, self.installed_version))
            db.commit()
            db.close()

    def system_needs_upgrade(self):
        return self.installed_version < self.version
        
    def do_db_upgrade(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('UPDATE system SET value=%s WHERE name=%s',
                       (self.version, self.name))
        db.commit()
        db.close()

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
        return not (self.config.get(section, 'client'))
    
    def do_ticket_field_upgrade(self):
        section = 'ticket-custom'
        
        self.config.set(section,'client', 'select')
        if not self.config.get(section, 'client.order'):
            self.config.set(section, 'client.order', '1')
        self.config.set(section,'client.options', 'enum:client')
        self.config.set(section,'client.label', 'Client')
        self.config.set(section,'client.value', '0')

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
        self.do_db_upgrade()
        print ' * Upgrading reports'
        self.do_reports_upgrade()

        if self.ticket_fields_need_upgrade():
            print ' * Upgrading fields'
            self.do_ticket_field_upgrade()

        print 'Done Upgrading'

