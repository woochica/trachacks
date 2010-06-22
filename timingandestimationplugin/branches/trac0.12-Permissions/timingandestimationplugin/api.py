import re
import dbhelper
import time
from tande_filters import *
from reports_filter import *
from blackmagic import *
from ticket_daemon import *
from ticket_webui import *
from usermanual import *
from ticket_policy import *
from trac.log import logger_factory
from trac.ticket import ITicketChangeListener, Ticket
from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor, PermissionSystem
from webui import *
from query_webui import *
from reportmanager import CustomReportManager
from statuses import *
from reports import all_reports
from stopwatch import *

## report columns
## id|author|title|query|description

class TimeTrackingSetupParticipant(Component):
    """ This is the config that must be there for this plugin to work:

        [ticket-custom]
        totalhours = text
        totalhours.value = 0
        totalhours.label = Total Hours

        billable = checkbox
        billable.value = 1
        billable.label = Is this billable?

        hours = text
        hours.value = 0
        hours.label = Hours to Add

        estimatedhours = text
        estimatedhours.value = 0
        estimatedhours.label = Estimated Hours?

        internal = checkbox
        internal.value = 0
        internal.label = Internal?

        """
    implements(IEnvironmentSetupParticipant)
    db_version_key = None
    db_version = None
    db_installed_version = None

    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""
    def __init__(self):
        # Setup logging
        self.statuses_key = 'T&E-statuses'
        self.db_version_key = 'TimingAndEstimationPlugin_Db_Version'
        self.db_version = 8
        # Initialise database schema version tracking.
        self.db_installed_version = dbhelper.get_system_value(self.env, \
            self.db_version_key) or 0

    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)


    def system_needs_upgrade(self):
        return self.db_installed_version < self.db_version

    def do_db_upgrade(self):
        if self.db_installed_version < 1:
            print "Creating bill_date table"
            sql = """
            CREATE TABLE bill_date (
            time integer,
            set_when integer,
            str_value text
            );
            """
            dbhelper.execute_non_query(self.env,  sql)


        if self.db_installed_version < 5:
            if dbhelper.db_table_exists(self.env, 'report_version'):
                print "Dropping report_version table"
                sql = "DELETE FROM report " \
                    "WHERE author=%s AND id IN (SELECT report FROM report_version)"
                dbhelper.execute_non_query(self.env, sql, 'Timing and Estimation Plugin')

                sql = "DROP TABLE report_version"
                dbhelper.execute_non_query(self.env, sql)

        #version 6 upgraded reports


        if self.db_installed_version < 7:
            field_settings = "field settings"
            self.config.set( field_settings, "fields", "billable, totalhours, hours, estimatedhours, internal" )
            self.config.set( field_settings, "billable.permission", "TIME_VIEW:hide, TIME_RECORD:disable" )
            self.config.set( field_settings, "hours.permission", "TIME_VIEW:remove, TIME_RECORD:disable" )
            self.config.set( field_settings, "estimatedhours.permission", "TIME_RECORD:disable" )
            self.config.set( field_settings, "internal.permission", "TIME_RECORD:hide")

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # This statement block always goes at the end this method
        dbhelper.set_system_value(self.env, self.db_version_key, self.db_version)
        self.db_installed_version = self.db_version
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

            

    def reports_need_upgrade(self):
        mgr = CustomReportManager(self.env, self.log)
        db_reports = mgr.get_version_hash_by_group(CustomReportManager.TimingAndEstimationKey)
        py_reports = {}
        for report_group in all_reports:
            for report in report_group['reports']:
                py_reports[report['uuid']]= report['version']
        
        diff = [(uuid, version) for (uuid, version) in py_reports.items()
                if not db_reports.has_key(uuid) or int(db_reports[uuid]) < int(version)]
                
        if len(diff) > 0:
            self.log.debug ("T&E needs upgrades for the following reports: %s" %
                            (diff, ))
        return len(diff) > 0

    def do_reports_upgrade(self, force=False):
        self.log.debug( "Beginning Reports Upgrade");
        mgr = CustomReportManager(self.env, self.log)
        statuses = get_statuses(self.env)
        stat_vars = status_variables(statuses)

        for report_group in all_reports:
            rlist = report_group["reports"]
            group_title = report_group["title"]
            for report in rlist:
                title = report["title"]
                new_version = report["version"]

                sql = report["sql"].replace('#STATUSES#', stat_vars)
                mgr.add_report(report["title"], "Timing and Estimation Plugin", \
                               "Reports Must Be Accessed From the Management Screen",
                               sql, report["uuid"], report["version"],
                               CustomReportManager.TimingAndEstimationKey,
                               group_title, force)

    def ticket_fields_need_upgrade(self):
        ticket_custom = "ticket-custom"
        return not ( self.config.get( ticket_custom, "totalhours" ) and \
                         self.config.get( ticket_custom, "hours" ) and \
                         self.config.get( ticket_custom, "totalhours.order") and \
                         self.config.get( ticket_custom, "hours.order") and \
                         self.config.get( ticket_custom, "estimatedhours.order") and \
                         self.config.get( ticket_custom, "estimatedhours") and \
                         self.config.get( ticket_custom, "internal") and \
                         "InternalTicketsPolicy" in self.config.getlist("trac", "permission_policies"))

    def do_ticket_field_upgrade(self):
        ticket_custom = "ticket-custom"

        if not self.config.get(ticket_custom,"totalhours"):
            self.config.set(ticket_custom,"totalhours", "text")
            self.config.set(ticket_custom,"totalhours.order", "4")
            self.config.set(ticket_custom,"totalhours.value", "0")
            self.config.set(ticket_custom,"totalhours.label", "Total Hours")


        if not self.config.get(ticket_custom,"billable"):
            self.config.set(ticket_custom,"billable", "checkbox")
            self.config.set(ticket_custom,"billable.value", "1")
            self.config.set(ticket_custom,"billable.order", "3")
            self.config.set(ticket_custom,"billable.label", "Billable?")

        if not self.config.get(ticket_custom,"hours"):
            self.config.set(ticket_custom,"hours", "text")
            self.config.set(ticket_custom,"hours.value", "0")
            self.config.set(ticket_custom,"hours.order", "2")
            self.config.set(ticket_custom,"hours.label", "Add Hours to Ticket")

        if not self.config.get(ticket_custom,"estimatedhours"):
            self.config.set(ticket_custom,"estimatedhours", "text")
            self.config.set(ticket_custom,"estimatedhours.value", "0")
            self.config.set(ticket_custom,"estimatedhours.order", "1")
            self.config.set(ticket_custom,"estimatedhours.label", "Estimated Number of Hours")

        if not self.config.get( ticket_custom, "internal"):
            self.config.set(ticket_custom, "internal", "checkbox")
            self.config.set(ticket_custom, "internal.value", "0")
            self.config.set(ticket_custom, "internal.label", "Internal?")
            self.config.set(ticket_custom,"internal.order", "5")

        if "InternalTicketsPolicy" not in self.config.getlist("trac", "permission_policies"):
            perms = ["InternalTicketsPolicy"]
            other_policies = self.config.getlist("trac", "permission_policies")
            if "DefaultPermissionPolicy" not in other_policies:
                perms.append("DefaultPermissionPolicy")
            perms.extend( other_policies )
            self.config.set("trac", "permission_policies", ', '.join(perms))

        self.config.save();

    def needs_user_man(self):
        maxversion = dbhelper.get_scalar(
            self.env, "SELECT MAX(version) FROM wiki WHERE name like %s", 0,
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
        dbhelper.execute_non_query(self.env, sql,
                                   user_manual_wiki_title,
                                   user_manual_version,
                                   when,
                                   user_manual_content)


    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.

        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.

        """
        sysUp = self.system_needs_upgrade()
        # Dont check for upgrades that will break the transaction
        # If we dont have a system, then everything needs to be updated
        res = (sysUp,
               sysUp or self.reports_need_upgrade(),
               sysUp or self.have_statuses_changed(),
               sysUp or self.ticket_fields_need_upgrade(),
               sysUp or self.needs_user_man())
        self.log.debug("T&E NEEDS UP?: sys:%s, rep:%s, stats:%s, fields:%s, man:%s" % \
                       res)
        r = False;
        for i in res: r |= i
        return r

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.

        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        def p(s):
            print s
            return True
        print "Timing and Estimation needs an upgrade"
        p("Upgrading Database")
        self.do_db_upgrade()
        p("Upgrading reports")
        self.do_reports_upgrade(force=self.have_statuses_changed())

        #make sure we upgrade the statuses string so that we dont need to always rebuild the
        # reports
        stats = get_statuses(self.env)
        val = ','.join(list(stats))
        dbhelper.set_system_value(self.env, self.statuses_key, val)

        if self.ticket_fields_need_upgrade():
            p("Upgrading fields")
            self.do_ticket_field_upgrade()
        if self.needs_user_man():
            p("Upgrading usermanual")
            self.do_user_man_update()
        print "Done Upgrading"

    def have_statuses_changed(self):
        """get the statuses from the last time we saved them,
        compare them to the ones we have now (ignoring '' and None),
        if we have different ones, throw return true
        """
        s = dbhelper.get_system_value(self.env, self.statuses_key)
        if not s:
            return True
        sys_stats = get_statuses(self.env)
        s = s.split(',')
        sys_stats.symmetric_difference_update(s)
        sys_stats.difference_update(['', None])
        return len(sys_stats) > 0
