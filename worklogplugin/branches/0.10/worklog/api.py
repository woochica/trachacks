import re
import time
from usermanual import *
from trac.log import logger_factory
from trac.ticket import ITicketChangeListener, Ticket
from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor, PermissionSystem
from webui import * 
from webadminui import * 
from uihooks_ticket import *
from timeline_hook import *
from ticket_daemon import *
try:
    from xmlrpc import *
except:
    pass

   
class WorkLogSetupParticipant(Component):
    implements(IEnvironmentSetupParticipant)

    db_version_key = None
    db_version = None
    db_installed_version = None
    
    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""
    def __init__(self):
        self.db_version_key = 'WorklogPlugin_Db_Version'
        self.db_version = 2
        self.db_installed_version = None

        # Initialise database schema version tracking.
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name=%s", (self.db_version_key,))
        try:
            self.db_installed_version = int(cursor.fetchone()[0])
        except:
            self.db_installed_version = 0
            cursor.execute("INSERT INTO system (name,value) VALUES(%s,%s)",
                           (self.db_version_key, self.db_installed_version))
            db.commit()
            db.close()

    
    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)
            
    def system_needs_upgrade(self):
        return self.db_installed_version < self.db_version
        
    def do_db_upgrade(self):
        # Legacy support hack (supports upgrades from revisions r2495 or before)
        if self.db_installed_version == 0:
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            try:
                cursor.execute('SELECT * FROM work_log LIMIT 1')
                # We've succeeded so we actually have version 1
                self.db_installed_version = 1
            except:
                pass
            db.close()
        # End Legacy support hack

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Do the staged updates
        try:
            if self.db_installed_version < 1:
                print 'Creating work_log table'
                cursor.execute('CREATE TABLE work_log ('
                               'user       TEXT,'
                               'ticket     INTEGER,'
                               'lastchange INTEGER,'
                               'starttime  INTEGER,'
                               'endtime    INTEGER'
                               ')')

            if self.db_installed_version < 2:
                print 'Updating work_log table (v2)'
                cursor.execute('ALTER TABLE work_log '
                               'ADD COLUMN comment TEXT')

            #if self.db_installed_version < 3:
            #    print 'Updating work_log table (v3)'
            #    cursor.execute('...')
            
            # Updates complete, set the version
            cursor.execute("UPDATE system SET value=%s WHERE name=%s", 
                           (self.db_version, self.db_version_key))
            db.commit()
            db.close()
        except Exception, e:
            self.log.error("WorklogPlugin Exception: %s" % (e,));
            db.rollback()


    
    def needs_user_man(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute('SELECT MAX(version) FROM wiki WHERE name=%s', (user_manual_wiki_title,))
            maxversion = int(cursor.fetchone()[0])
        except:
            maxversion = 0
        db.close()

        return maxversion < user_manual_version

    def do_user_man_update(self):
        when = int(time.time())
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('INSERT INTO wiki (name,version,time,author,ipnr,text,comment,readonly) '
                       'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                       (user_manual_wiki_title, user_manual_version, when,
                        'WorkLog Plugin', '127.0.0.1', user_manual_content,
                        '', 0))
        db.commit()
        db.close()
        
    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.

        """
        return (self.system_needs_upgrade() \
                or self.needs_user_man())
            
    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        def p(s):
            print s
            return True
        print "Worklog needs an upgrade"
        if self.system_needs_upgrade():
            p("Upgrading Database")
            self.do_db_upgrade()
        if self.needs_user_man():
            p("Upgrading usermanual")
            self.do_user_man_update()
        print "Done upgrading Worklog"




