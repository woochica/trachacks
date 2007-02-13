import time
import sys
from datetime import date, datetime

# Trac 0.11
#from genshi.builder import tag

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import escape, Markup, format_date

class ScrumComponent(Component):
    implements(IEnvironmentSetupParticipant, INavigationContributor,
               IRequestHandler, ITemplateProvider, IPermissionRequestor)
    
    #---------------------------------------------------------------------------
    # IEnvironmentSetupParticipant methods
    #---------------------------------------------------------------------------
    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        needsUpgrade = False
        try:
            cursor.execute("SELECT * FROM ticket_work LIMIT 1;")
        except:
            needsUpgrade = True
        return needsUpgrade

    def upgrade_environment(self, db):
        cursor = db.cursor()

        try:
            cursor.execute("SELECT started FROM milestone LIMIT 1;")
        except:
            self.log.info("Adding column 'started' to the milestone table...")
            cursor.execute("ALTER TABLE milestone ADD COLUMN started integer DEFAULT 0;")
            cursor.execute("""
                ALTER TABLE milestone
                ADD CONSTRAINT check_time CHECK (completed<1 OR started<=completed);""")

        self.log.info("Creating trac_date function...")
        cursor.execute("""
          CREATE OR REPLACE FUNCTION trac_date(seconds int4)
            RETURNS timestamp AS
          $BODY$select 'epoch'::timestamp +$1* INTERVAL '1 second'$BODY$
            LANGUAGE 'sql' IMMUTABLE;""")
        
        self.log.info("Creating first_value function...")
        cursor.execute("""
          CREATE OR REPLACE FUNCTION first_value(int4, text)
            RETURNS text AS          
          $BODY$          
          select value          
          from          
          (          
            select ticket.time, oldvalue as value          
            from ticket, ticket_change          
            where id=ticket and ticket=$1 and field=$2          
            union          
            select ticket.time, value          
            from ticket, ticket_custom          
            where id=ticket and ticket=$1 and name=$2          
          ) as tbl          
          order by time asc          
          $BODY$          
            LANGUAGE 'sql' STABLE;""")
        
        self.log.info("Creating value_at_t function...")
        cursor.execute("""
          CREATE OR REPLACE FUNCTION value_at_t(int4, text, int4)
            RETURNS text AS          
          $BODY$          
            select value          
            from          
            (          
              select ticket_change.time, newvalue as value          
              from ticket_change          
              where ticket=$1 and field=$2 and ticket_change.time<=$3          
              union          
              select ticket.time, first_value($1, $2) as value          
              from ticket          
              where ticket.id=$1 and ticket.time<=$3          
            ) as tbl          
            order by time desc          
          $BODY$          
            LANGUAGE 'sql' STABLE;""")

        self.log.info("Creating ticket_work view...")
        cursor.execute("""
          CREATE OR REPLACE VIEW ticket_work AS  
            SELECT t.id AS ticket, sum(
                   CASE
                       WHEN c.name = 'estimatedwork' THEN c.value::real
                       ELSE 0
                   END) AS estimatedwork, sum(
                   CASE
                       WHEN c.name = 'workdone' THEN c.value::real
                       ELSE 0
                   END) AS workdone
              FROM ticket t
              LEFT JOIN ticket_custom c ON t.id = c.ticket
             WHERE c.name = 'estimatedwork' OR c.name = 'workdone'
             GROUP BY t.id;""")
        
        self.log.info("Creating milestone_work view...")
        cursor.execute("""
          CREATE OR REPLACE VIEW milestone_work AS 
            SELECT t.milestone, sum(w.estimatedwork) AS estimatedwork,          
                   sum(w.workdone) AS workdone          
              FROM ticket t, ticket_work w          
             WHERE t.id = w.ticket          
             GROUP BY t.milestone;""")
        
        self.log.info("Creating milestone_dates view...")
        cursor.execute("""
          CREATE OR REPLACE VIEW milestone_dates AS 
            SELECT m.*, COALESCE(NULLIF(m.completed, 0), NULLIF(m.due, 0)) AS end_date
              FROM milestone m;""")

        self.log.info("Creating milestone_progress view...")
        cursor.execute("""
          CREATE OR REPLACE VIEW milestone_progress AS
            SELECT t.milestone, c.time, (
              SELECT sum(value_at_t(t_at_t.id, 'estimatedwork', c.time)::real) AS sum
                FROM ticket t_at_t
               WHERE t_at_t.milestone = t.milestone
               GROUP BY t_at_t.milestone) AS estimatedwork, (
              SELECT sum(value_at_t(t_at_t.id, 'workdone', c.time)::real) AS sum
                FROM ticket t_at_t
               WHERE t_at_t.milestone = t.milestone
               GROUP BY t_at_t.milestone) AS workdone
            FROM ticket t LEFT JOIN milestone_dates m ON t.milestone = m.name, ticket_change c
            WHERE t.id = c.ticket AND (c.field = 'estimatedwork' OR c.field = 'workdone')
            GROUP BY t.milestone, c.time
            ORDER BY t.milestone, c.time;""")
        
        self.log.info("Creating end_milestone_workdone view...")
        cursor.execute("""
          CREATE OR REPLACE VIEW end_milestone_workdone AS
            SELECT m.*, sum(value_at_t(t.id, 'workdone', end_date)::real) AS workdone
              FROM milestone_dates m LEFT JOIN ticket t on t.milestone = m.name
             WHERE t.status = 'closed'          
             GROUP BY m.name, m.due, m.completed, m.description, m.started, m.end_date;""")

        self.log.info("Creating end_milestone_estimatedwork view...")
        cursor.execute("""
          CREATE OR REPLACE VIEW end_milestone_estimatedwork AS
            SELECT m.*,
                   sum(value_at_t(t.id, 'estimatedwork', end_date)::real) AS estimatedwork
              FROM milestone_dates m LEFT JOIN ticket t on t.milestone = m.name
             GROUP BY m.name, m.due, m.completed, m.description, m.started, m.end_date;""")
            
        self.log.info("Creating milestone_stats view...")
        cursor.execute("""
          CREATE OR REPLACE VIEW milestone_stats AS
            SELECT m1.*, m2.estimatedwork, workdone*60*60*24 / (m1.end_date - m1.started) AS velocity,
                   (SELECT count(DISTINCT c.author)         
                      FROM ticket t LEFT JOIN ticket_change c ON t.id = c.ticket          
                     WHERE t.milestone = m1.name AND c.field = 'workdone' AND
                           c.time>=m1.started AND c.time<=m1.end_date) AS engineers
              FROM end_milestone_workdone m1, end_milestone_estimatedwork m2
             WHERE m1.name = m2.name;""")

        self.log.info("Creating reports...")
        cursor.execute("DELETE FROM report WHERE author='scrumplugin';")
        
        reports = [
          [
            "Ticket work by milestone",
            "Lists the work estimated and done for each ticket, grouping them by milestone.",
            """
SELECT milestone as __group__, __style__, __color__, ticket,
       summary, status, type, owner, estimatedwork as "Estimated work",
       workdone as "Work done", __ord__
  FROM
  
    (SELECT 0 as __ord__, p.value AS __color__,
            (CASE status 
             WHEN 'closed' THEN 'color: #777; background: #ddd; border-color: #ccc;'
             ELSE 
              (CASE owner
               WHEN '$USER' THEN 'font-weight: bold'
               END)
            END) AS __style__,
            cast(t.id as text) AS ticket, summary, status, t.type, priority, owner,
       milestone, estimatedwork, workdone
       FROM ticket t, enum p, ticket_work w
      WHERE p.name=t.priority AND p.type='priority' AND t.id=w.ticket

    UNION

    SELECT 1 as __ord__, null AS __color__, 'background-color:#DFE;' as __style__,
           '' AS ticket, '' as summary, '' as status, '' as type,
           '' as priority, 'Total:' as owner, milestone,
           estimatedwork, workdone
      FROM milestone_work

) as tbl
ORDER BY milestone, __ord__, __color__;"""
          ],
          [
            "Daily milestone progress",
            "Lists the changes in work estimated and done during a each milestone.",
            """
SELECT milestone AS __group__, 0 AS __order__, (time/(60*60*24))*60*60*24 AS modified,
       MAX(estimatedwork) AS estimatedwork, MIN(workdone) AS workdone
FROM milestone_progress m
GROUP BY milestone, modified;"""
          ],
          [
            "Milestone dates and statistics",
            "",
            """
SELECT name, description, trac_date(started)::date::text AS "Begin",
       trac_date(end_date)::date::text AS "End", estimatedwork as "Estimated work",
       workdone AS "Work done", ROUND(velocity) as velocity, engineers,
       CASE WHEN engineers<>0 THEN ROUND(velocity/engineers) ELSE NULL END AS "Velocity per Eng" 
FROM milestone_stats
ORDER BY started, end_date;"""
          ]
        ]
        
        cursor.executemany("""
          INSERT INTO report (author, title, description, query) 
          VALUES ('scrumplugin', %s, %s, %s);""", reports)
            
        db.commit()  

    #---------------------------------------------------------------------------
    # INavigationContributor methods
    #---------------------------------------------------------------------------
    def get_active_navigation_item(self, req):
        return 'scrum'
                
    def get_navigation_items(self, req):
        yield 'mainnav', 'scrum', Markup('<a href="%s">Charts</a>', (req.href.scrum()))
# Trac 0.11
#        yield 'mainnav', 'scrum', tag.a('Scrum', href=req.href.scrum(), title='Scrum')
        
    #---------------------------------------------------------------------------
    # IPermissionRequestor methods
    #---------------------------------------------------------------------------
    def get_permission_actions(self):
        return ["SCRUM_VIEW"]

    #---------------------------------------------------------------------------
    # IRequestHandler methods
    #---------------------------------------------------------------------------
    def match_request(self, req):
        return req.path_info == '/scrum'
    
    def process_request(self, req):
        req.perm.assert_permission('SCRUM_VIEW')
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute("SELECT name FROM milestone;")
        milestone_lists = cursor.fetchall()
        milestones = []
        for mile in milestone_lists:
            milestones.append(mile[0])
            
        selected_milestone = req.args.get('selected_milestone', milestones[0])
        
        # expose display data to the clearsilver templates
        req.hdf['milestones'] = milestones
        req.hdf['selected_milestone'] = selected_milestone
        req.hdf['draw_graph'] = False
        req.hdf['start_complete'] = False
        
        if req.perm.has_permission("MILESTONE_MODIFY"):
            req.hdf['start_complete'] = True # show the start and complete milestone buttons to admins
        
        if req.args.has_key('start'):
            self.setMilestoneDate(db, selected_milestone, "started", time.time())
        elif req.args.has_key('complete'):
            self.setMilestoneDate(db, selected_milestone, "completed", time.time())

        req.hdf['datasets.estimatedwork'] = self.getTimeSeries(db, selected_milestone, 'estimatedwork' )
        req.hdf['datasets.workdone'] = self.getTimeSeries(db, selected_milestone, 'workdone' )
        req.hdf['milestone.begin'] = self.getMilestoneDate(db, selected_milestone, 'started')
        end = int(self.getMilestoneDate(db, selected_milestone, 'completed'))
        if end<1:
            end = int(self.getMilestoneDate(db, selected_milestone, 'due'))
        if end<1:
            end = int(time.time())
        req.hdf['milestone.end'] = end 
        add_stylesheet(req, 'hw/css/projectcharts.css')
        return 'projectcharts.cs', None
        
    def getTimeSeries(self, db, selected_milestone, field_name):
        cursor = db.cursor()
        sql = "SELECT time, " + field_name + """
                 FROM milestone_progress
                WHERE milestone = %s
                ORDER BY time"""
        cursor.execute(sql, [ selected_milestone ] )
        list_of_tuples = cursor.fetchall()
        list_of_lists = []
        for i in list_of_tuples:
            list_of_lists.append(list(i))
        return list_of_lists

    def getMilestoneDate(self, db, milestone, date_attr_name):
        cursor = db.cursor()
        cursor.execute("SELECT " + date_attr_name + " FROM milestone WHERE name=%s;", [ milestone ] )
        row = cursor.fetchone()
        if row:
          return row[0]
        else:
          return null

    def setMilestoneDate(self, db, milestone, date_attr_name, t):
        old_t = self.getMilestoneDate(db, milestone, date_attr_name)
        if old_t and old_t > 0 :
            raise TracError("Milestone '%s' was already %s on %s" % (milestone, date_attr_name, format_date(int(old_t))))
        cursor = db.cursor()
        sql = "UPDATE milestone SET " + date_attr_name + "=%s WHERE name=%s"
        cursor.execute(sql, ( str(int(t)), milestone ) )
        db.commit()
                
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
