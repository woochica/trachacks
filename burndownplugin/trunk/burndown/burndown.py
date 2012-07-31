# Burndown plugin
#
# Author: Gunther Seghers (gunther.seghers@ipc.be)
#

import time
import calendar
import datetime
import sys

from trac.core import *
from trac.config import BoolOption
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import escape, Markup, format_date
from trac.ticket import ITicketChangeListener

class BurndownComponent(Component): 
    implements(IEnvironmentSetupParticipant, INavigationContributor,
               IRequestHandler, ITemplateProvider, IPermissionRequestor) 
    
    #---------------------------------------------------------------------------
    # IEnvironmentSetupParticipant methods
    #---------------------------------------------------------------------------
    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        needsUpgrade = False
        return needsUpgrade

    def upgrade_environment(self, db):
        print >> sys.stderr, 'No upgrade required'
            
    #---------------------------------------------------------------------------
    # INavigationContributor methods
    #---------------------------------------------------------------------------
    def get_active_navigation_item(self, req):
        return "burndown"

    def get_navigation_items(self, req):
        if req.perm.has_permission("BURNDOWN_VIEW"):
            yield 'mainnav', 'burndown', Markup('<a href="%s">Burndown</a>', self.env.href.burndown())

    #---------------------------------------------------------------------------
    # IPermissionRequestor methods
    #---------------------------------------------------------------------------
    def get_permission_actions(self):
        return ["BURNDOWN_VIEW"]

    #---------------------------------------------------------------------------
    # IRequestHandler methods
    #---------------------------------------------------------------------------
    def match_request(self, req):
        return req.path_info == '/burndown'
    
    def process_request(self, req):
        req.perm.assert_permission('BURNDOWN_VIEW')
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute("SELECT name FROM milestone")
        milestone_lists = cursor.fetchall()
        milestones = []
        for mile in milestone_lists:
            milestones.append(mile[0])
       
        if (milestones and milestones[0]):
            selected_milestone = req.args.get('selected_milestone', milestones[0])
        else:
            selected_milestone = ''
        
        # Expose display data to the Clearsilver templates
        req.hdf['milestones'] = milestones        
        req.hdf['selected_milestone'] = selected_milestone       
        
        burndown = self.get_burndown_data(db, selected_milestone)        
        
        # Build XML data for FCF_MSColumn3D.swf
        dataXML = "<graph xaxisname='Day' yaxisname='Time' "\
                      "hovercapbg='DEDEBE' hovercapborder='889E6D' rotateNames='1' showValues='1' animation='1' "
        if burndown[0][0] == 'N/A':
            dataXML += "yAxisMaxValue='100' "                                 
        dataXML += "numdivlines='9' divLineColor='CCCCCC' divLineAlpha='80' decimalPrecision='2' "\
                   "showAlternateVGridColor='1' AlternateVGridAlpha='30' AlternateVGridColor='CCCCCC' "\
                   "caption='Burndown'> <categories font='Arial' fontSize='11' fontColor='000000'>"
        for b in burndown:
            dataXML += "<category name='%s'/>" %b[0]
        dataXML +="</categories>"
        dataXML +="<dataset seriesname='Estimated' color='FDC12E' alpha='70'>"
        for b in burndown:
            dataXML +="<set value='%s' />" % b[1]
        dataXML +="</dataset>"
        dataXML +="<dataset seriesname='Performed' color='56B9F9' showValues='1' alpha='70'>"
        for b in burndown:
            dataXML +="<set value='%s' />" % b[2]
        dataXML +="</dataset></graph>"           
        req.hdf['dataXML'] = dataXML
        
        add_stylesheet(req, 'hw/css/burndown.css')
        return 'burndown.cs', None
    
    
    def get_burndown_data(self,db, selected_milestone):
        
        # Iteration period
        cursor = db.cursor()
        sqlIterationPeriod = "SELECT min(tc.time) , max(tc.time) FROM ticket_change tc "\
                             "WHERE tc.field = 'hours' "\
                             "AND tc.ticket in ( select id from ticket where milestone = '%s');" %  selected_milestone            
        cursor.execute(sqlIterationPeriod)                        
        iterationPeriod= cursor.fetchall()

        
        if (not iterationPeriod  or not iterationPeriod[0][0]): 
            return [["N/A",0,0]]
                
        """ Total hours performed per day 
        sqlHoursPerDay = " SELECT tc.time / (24*3600), sum(tc.newvalue) "\
                       " FROM ticket_change tc "\
                       " WHERE tc.ticket in ( select id from ticket where milestone = '%s' ) "\
                       " AND tc.field = 'hours' "\
                       " GROUP BY  tc.time / (24*3600) "\
                       " ORDER BY tc.time / (24*3600);" % (selected_milestone)     
        cursor.execute(sqlHoursPerDay)                         
        hoursPerDay = cursor.fetchall()                       
        """
               
        # Total hours performed so far per day 
        sqlTotalHoursPerDay = " SELECT day, sum(totalhours) "\
                       " FROM ( SELECT tc.time / (24*3600) day, tc.ticket, substr(max( tc.time||':'||tc.newvalue),12, 50 ) totalhours "\
                              " FROM ticket_change tc "\
                              " WHERE tc.ticket in ( select id from ticket where milestone =  '%s')"\
                              " AND tc.field = 'totalhours' "\
                              " GROUP BY tc.time / (24*3600), tc.ticket ) GROUP BY day ORDER BY day;" % (selected_milestone)
        cursor.execute(sqlTotalHoursPerDay)                         
        totalHoursPerDay = cursor.fetchall()                       
        
        # Total work estimated at start of iteration => tc.time<iteration[0][0]
        # 1. Latest updates before iteration start
        sqlEstimates = " SELECT sum(estimate) "\
                       " FROM ( SELECT tc.ticket, substr(max( tc.time||':'||tc.newvalue),12, 50 ) estimate "\
                              " FROM ticket_change tc "\
                              " WHERE tc.ticket in ( select id from ticket where milestone =  '%s')"\
                              " AND tc.field = 'estimatedhours' "\
                              " AND tc.time < %d "\
                              " GROUP BY tc.ticket  " % ( selected_milestone, iterationPeriod[0][0])
        sqlEstimates = sqlEstimates + " UNION "
        # 2. Previous estimates when updated after iteration start 
        sqlEstimates = sqlEstimates + "SELECT tc.ticket, substr(min( tc.time||':'||tc.oldvalue),12, 50 ) estimate "\
                              " FROM ticket_change tc "\
                              " WHERE tc.ticket in ( select id from ticket where milestone =  '%s')"\
                              " AND tc.field = 'estimatedhours' "\
                              " AND tc.time > %d "\
                              " GROUP BY tc.ticket  " % ( selected_milestone, iterationPeriod[0][0])
        sqlEstimates = sqlEstimates + " UNION "                
        # 3. Original estimates  when never updated              
        sqlEstimates = sqlEstimates + "SELECT ticket, value estimate "\
                       "FROM ticket_custom "\
                       "WHERE name = 'estimatedhours' "\
                       "AND ticket in (select id from ticket where milestone='%s') "\
                       "AND ticket not in (select ticket from ticket_change) ) " % ( selected_milestone )                                    
        cursor.execute(sqlEstimates)
        estimates = cursor.fetchall()        
        
        # Estimation updates per day          
        sqlEstimationUpdates = " SELECT day, sum(estimate) "\
                         " FROM ( SELECT tc.time / (24*3600) day, tc.ticket, substr(max( tc.time||':'||(tc.newvalue - tc.oldvalue)),12, 50 ) estimate "\
                              " FROM ticket_change tc "\
                              " WHERE tc.ticket in ( select id from ticket where milestone =  '%s')"\
                              " AND tc.field = 'estimatedhours' "\
                              " GROUP BY tc.time / (24*3600), tc.ticket ) GROUP BY day ORDER by day;" % (selected_milestone)                                    
        cursor.execute(sqlEstimationUpdates)
        estimationUpdates = cursor.fetchall()
            
        
        # Build list with estimations and zero hours performed      
        
        iterationStart = iterationPeriod[0][0] / (24*3600)
        iterationEnd = iterationPeriod[0][1]  / (24*3600)
        if (estimates and estimates[0][0]):
            initialEstimation = estimates[0][0] 
        else:
            initialEstimation = 0
            
        burndown = []
        for day in range ( 0, iterationEnd - iterationStart + 1):
            secSinceEpoch = iterationPeriod[0][0]+ day*(24*3600)
            burndown.append([secSinceEpoch, initialEstimation,0])
            # Add possible re-estimates            
            if estimationUpdates :
                for estimationUpdate in estimationUpdates:
                    if estimationUpdate[0]*(24*3600) <= secSinceEpoch:
                        if estimationUpdate[1]:
                            burndown[ day ][1] += estimationUpdate[1]                 
        
        # Add hours performed   
        if totalHoursPerDay:
            for hoursPerformed in totalHoursPerDay:
                for day in range ( 0, iterationEnd - iterationStart + 1):
                    secSinceEpoch = iterationPeriod[0][0]+ day*(24*3600)
                    if  hoursPerformed[0]*(24*3600) <= secSinceEpoch:
                        burndown[day][2] = hoursPerformed[1]
        
        # Convert day into yyyy/mm/dd string 
        for day in range ( 0, iterationEnd - iterationStart + 1):
            daytime = iterationPeriod[0][0]+ day*(24*3600)
            yyyymmdd = time.strftime("%m/%d", time.gmtime(daytime))
            burndown[day][0] = yyyymmdd
        
        #print 'TEST - Burndown              = ' , burndown 
        #print 'TEST - Iteration             = ' , iterationPeriod
        #print 'TEST - totalHoursPerformed   = ' , totalHoursPerDay
        #print 'TEST - estimates             = ' , estimates
        #print 'TEST - re-estimates          = ' , estimationUpdates
                           
        return burndown 
        
    #---------------------------------------------------------------------------
    # ITemplateProvider methods
    #---------------------------------------------------------------------------
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('hw', resource_filename(__name__, 'htdocs'))]


