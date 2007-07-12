import re
import dbhelper
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

   
class WorkLogSetupParticipant(Component):
    implements(IEnvironmentSetupParticipant)
    
    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""
    def __init__(self):
        pass
    
    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)
            
    def db_needs_upgrade(self):
        work_log = dbhelper.db_table_exists(self.env.get_db_cnx(), 'work_log');
        return not work_log
        
    def db_do_upgrade(self):
        work_log = dbhelper.db_table_exists(self.env.get_db_cnx(), 'work_log');
        if not work_log:
            print "Creating work_log table"
            sql = """
            CREATE TABLE work_log (
            user text,
            ticket integer,
            lastchange integer,
            starttime integer,
            endtime integer
            );
            """
            dbhelper.execute_non_query(self.env.get_db_cnx(), sql)
    
    def needs_user_man(self):
        maxversion = dbhelper.get_scalar(self.env.get_db_cnx(),
                                         "SELECT MAX(version) FROM wiki WHERE name like %s", 0,
                                         user_manual_wiki_title)
        if (not maxversion) or maxversion < user_manual_version:
            return True
        return False

    def do_user_man_update(self):

        when = int(time.time())
        sql = """
        INSERT INTO wiki (name,version,time,author,ipnr,text,comment,readonly)
        VALUES ( %s, %s, %s, 'Timing and Estimation Plugin', '127.0.0.1', %s,'',0)
        """
        dbhelper.execute_non_query(self.env.get_db_cnx(),sql,
                                   user_manual_wiki_title,
                                   user_manual_version,
                                   when,
                                   user_manual_content)
            
        
    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.

        """
        return (self.db_needs_upgrade() \
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
        if self.db_needs_upgrade():
            p("Upgrading Database")
            self.db_do_upgrade()
        if self.needs_user_man():
            p("Upgrading usermanual")
            self.do_user_man_update()
        print "Done upgrading Worklog"




