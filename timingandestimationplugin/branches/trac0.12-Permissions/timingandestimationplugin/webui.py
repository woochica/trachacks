from pkg_resources import resource_filename
import re
import time
import datetime
import dbhelper
from usermanual import *
from trac.core import *
from trac.web import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.util import Markup
from trac.web.chrome import add_stylesheet, add_script, \
     INavigationContributor, ITemplateProvider
from trac.web.href import Href
from reportmanager import CustomReportManager
from statuses import get_statuses
import datetime
import trac.util.datefmt
import reports

def strptime(date_string, format):
    return datetime.datetime(*(time.strptime(date_string, format)[0:6]))

#get_statuses = api.get_statuses
validTimeFormats=[
    '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %I:%M:%S.%f %p',
    '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %I:%M:%S %p',
    '%Y-%m-%d %H:%M', '%Y-%m-%d %I:%M %p',
    '%Y-%m-%d %H', '%Y-%m-%d %I %p',
    '%Y-%m-%d',
    
    '%Y/%m/%d %H:%M:%S.%f', '%Y/%m/%d %I:%M:%S.%f %p',
    '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %I:%M:%S %p',
    '%Y/%m/%d %H:%M', '%Y/%m/%d %I:%M %p',
    '%Y/%m/%d %H', '%Y/%m/%d %H %p',
    '%Y/%m/%d',
    
    '%Y.%m.%d %H:%M:%S.%f', '%Y.%m.%d %I:%M:%S.%f %p',
    '%Y.%m.%d %H:%M:%S', '%Y.%m.%d %I:%M:%S %p',
    '%Y.%m.%d %H:%M', '%Y.%m.%d %I:%M %p',
    '%Y.%m.%d %H', '%Y.%m.%d %I %p',
    '%Y.%m.%d',
    ]
def parsetime(val, tzinfo=trac.util.datefmt.to_datetime(None).tzinfo):
    if not val: return None
    val = val.strip()
    if not val: return None
    it = None
    for f in validTimeFormats:
        #print f, datetime.datetime.strptime(val, f)
        try: return strptime(val, f).replace(tzinfo=tzinfo)
        except ValueError: pass
    raise TracError('Unable to convert bill date %s to a time, please provide a date in yyyy-mm-dd hh:mm:ss format' % val)


class TimingEstimationAndBillingPage(Component):
    implements(IPermissionRequestor, INavigationContributor, IRequestHandler, ITemplateProvider)

    def __init__(self):
        pass

    # IPermissionRequestor methods 
    def get_permission_actions(self): 
        return ["TIME_VIEW", "TIME_RECORD", ("TIME_ADMIN", ["TIME_RECORD", "TIME_VIEW"])] 

    def set_bill_date(self, username="Timing and Estimation Plugin",  when=None):
        now = trac.util.datefmt.to_datetime(None)#get now
        if isinstance(when, str) or isinstance(when, unicode):
            when = parsetime(when, now.tzinfo)
        if not when: when = now

        strwhen = "%#04d-%#02d-%#02d %#02d:%#02d:%#02d" % \
                (when.year, when.month, when.day, when.hour,when.minute, when.second)

        sql = """
        INSERT INTO bill_date (time, set_when, str_value)
        VALUES (%s, %s, %s)
        """
        dbhelper.execute_non_query(self.env, sql, trac.util.datefmt.to_timestamp(when),
                                   trac.util.datefmt.to_timestamp(now), strwhen)


    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        val = re.search('/billing$', req.path_info)
        if val and val.start() == 0:
            return "billing"
        else:
            return ""

    def get_navigation_items(self, req):
        url = req.href.billing()
        if req.perm.has_permission("TIME_VIEW"):
            yield 'mainnav', "billing", \
                Markup('<a href="%s">%s</a>' % \
                           (url , "Time Reports"))

    # IRequestHandler methods
    def set_request_billing_dates(self, data):
        billing_dates = []
        billing_time_sql = """
        SELECT DISTINCT time as value, str_value as text
        FROM bill_date
        ORDER BY time DESC
        """
        rs = dbhelper.get_result_set(self.env, billing_time_sql)
        if rs:
            for (value, text) in rs.rows:
                billing_info = {'text':text , 'value':value*1000*1000}
                billing_dates.extend([billing_info]) 
        #self.log.debug("bill-dates: %s"%billing_dates)
        data['billing_info']["billdates"] = billing_dates

    def match_request(self, req):
        val = re.search('/billing$', req.path_info)
        return val and val.start() == 0

    def process_request(self, req):
        messages = []
        req.perm.require("TIME_VIEW")
        def addMessage(s):
            messages.extend([s]);

        if req.method == 'POST':
            req.perm.require("TIME_ADMIN")
            if req.args.has_key('setbillingtime'):
                self.set_bill_date(req.authname, req.args.get('newbilltime'))
                addMessage("All tickets last bill date updated")

        mgr = CustomReportManager(self.env, self.log)
        data = {};
        data["is_time_admin"] = req.perm.has_permission("TIME_ADMIN")
        data["statuses"] = get_statuses(self.env)
        data["reports"] = mgr.get_reports_by_group(CustomReportManager.TimingAndEstimationKey);
        # Handle pulling in report_descriptions
        # Could be added to custom report stuff, but that requires 
        # coordinating with too many people for me to care right now
        report_descriptions = {}
        for h in reports.all_reports:
            report_descriptions[h["title"]] = h["description"]
        for key in data["reports"]:
            if report_descriptions.has_key(key):
                data["reports"][key]["description"] = report_descriptions[key]
        #self.log.debug("DEBUG got %s, %s" % (data["reports"], type(data["reports"])));
        data["billing_info"] = {"messages":         messages,
                                "href":             req.href.billing(),
                                "report_base_href": req.href.report(),
                                "usermanual_href":  req.href.wiki(user_manual_wiki_title),
                                "usermanual_title": user_manual_title }

        self.set_request_billing_dates(data)

        add_stylesheet(req, "billing/billingplugin.css")
        add_script(req, "billing/date.js")
        add_script(req, "billing/linkifyer.js")
        return 'billing.html', data, None


    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('billing', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        genshi templates.
        """
        rtn = [resource_filename(__name__, 'templates')]
        return rtn

