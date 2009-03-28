# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 Bhuricha Sethanadha <khundeen@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac-hacks.org/wiki/TracMetrixPlugin.
#
# Author: Bhuricha Sethanandha <khundeen@gmail.com>

import re
from datetime import timedelta, datetime
from genshi.builder import tag
from trac import __version__
from trac import mimeview
from model import *  # need it but should have worked in __init__.py
from trac.config import ExtensionOption
from trac.mimeview import Context
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.ticket import Milestone, Ticket, model #These are object
from trac.ticket.query import Query
from trac.ticket.roadmap import ITicketGroupStatsProvider, DefaultTicketGroupStatsProvider, \
                                get_ticket_stats, get_tickets_for_milestone, \
                                milestone_stats_data, TicketGroupStats
from trac.util.compat import sorted
from trac.util.datefmt import utc
from trac.web import IRequestHandler, IRequestFilter
from trac.web.chrome import add_stylesheet, INavigationContributor, ITemplateProvider

# Constants
DAYS_BACK = 28

def get_project_tickets(env):
    """
        This method collect interesting data of each ticket in the project.
        
        lead_time is the time from when ticket is created until it is closed.
        closed_time is the time from wheh ticket is closed untill it is reopened.
        
    """
    
    cursor = env.get_db_cnx().cursor()
    
    cursor.execute("SELECT id FROM ticket ORDER BY id")

    tkt_ids = [id for id , in cursor]
    
    return tkt_ids

def last_day_of_month(year, month):

    # For december the next month will be january of next year.
    if month == 12: 
 	year = year + 1 
 	
    return datetime(year, (month%12)+1 , 1, tzinfo=utc) - timedelta(days=1)

class PDashboard(Component):

    implements(INavigationContributor, IPermissionRequestor, IRequestHandler, ITemplateProvider)
    stats_provider = ExtensionOption('pdashboard', 'stats_provider',
                                     ITicketGroupStatsProvider,
                                     'ProgressTicketGroupStatsProvider',
        """Name of the component implementing `ITicketGroupStatsProvider`, 
        which is used to collect statistics on groups of tickets for display
        in the project dashboard views.""")

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'pdashboard'

    def get_navigation_items(self, req):
        if 'ROADMAP_VIEW' in req.perm:
            yield ('mainnav', 'pdashboard',
                   tag.a('Dashboard', href=req.href.pdashboard()))

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['ROADMAP_VIEW']

    # IRequestHandler methods


    def match_request(self, req):

        self.env.log.info("pdashboard match request %s" % (req.path_info,))  
                
        urlcomp = req.path_info.split('/')
        if len(urlcomp) < 2:
            return False
        
        self.env.log.info(urlcomp)
        
        if len(urlcomp) >= 2:
            if urlcomp[1] == 'pdashboard' and len(urlcomp) >= 2:
                if len(urlcomp) == 3: #url has 2 
                    req.args['imagename'] = urlcomp[2]
                else:
                    req.args['imagename'] = None
                return True

    def process_request(self, req):
        req.perm.require('ROADMAP_VIEW')

        db = self.env.get_db_cnx()
        
        filename = req.args.get('imagename')
                    
        if filename != None:    
            
            self.env.log.info("request for image")
            path = os.path.join(self.env.path, 'cache', 'tracmetrixplugin', filename)
            req.send_file(path, mimeview.get_mimetype(path))
            
        else:
            
            self.env.log.info("request mdashboard")
            add_stylesheet(req, 'pd/css/dashboard.css')  
            
            return self._render_view(req, db) 
        

    def _render_view(self, req, db):
        
        showall = req.args.get('show') == 'all'
                
        # Get list of milestone object for the project
        milestones = list(Milestone.select(self.env, showall, db))
        stats = []
        queries = []

        for milestone in milestones:
            tickets = get_tickets_for_milestone(self.env, db, milestone.name,
                                                'owner')
            stat = get_ticket_stats(self.stats_provider, tickets)
            stats.append(milestone_stats_data(req, stat, milestone.name))

        project = {
            'name': self.env.project_name,
            'description': self.env.project_description
        }
        
        data = {
            'context': Context.from_request(req),
            'milestones': milestones,
            'milestone_stats': stats,
            'queries': queries,
            'showall': showall,
            'project' : project
        }
        
        tkt_stats = {}
        project_tickets = get_project_tickets(self.env)
        
        # Get project progress stats
        proj_stat = self.stats_provider.get_ticket_group_stats(project_tickets)
        
        data['proj_progress_stat'] = {'stats': proj_stat,
                                      'stats_href': req.href.query(proj_stat.qry_args),
                                      'interval_hrefs': [req.href.query(interval['qry_args'])
                                                         for interval in proj_stat.intervals]}

        closed_stat = self.stats_provider.get_ticket_resolution_group_stats(project_tickets)

        data['proj_closed_stat'] = {'stats': closed_stat,
                                      'stats_href': req.href.query(closed_stat.qry_args),
                                      'interval_hrefs': [req.href.query(interval['qry_args'])
                                                         for interval in closed_stat.intervals]}


        tkt_group_metrics = TicketGroupMetrics(self.env, project_tickets)      
        
        tkt_frequency_stats = tkt_group_metrics.get_frequency_metrics_stats()
        tkt_duration_stats = tkt_group_metrics.get_duration_metrics_stats()
        
        #stat for this month
        today = datetime.now()
        bmi_stats = []
        
        first_day = datetime(today.year, today.month, 1, tzinfo=utc)
        last_day = last_day_of_month(today.year, today.month)
        bmi_stats.append(tkt_group_metrics.get_bmi_monthly_stats(first_day, last_day))
         
        # stat for last month        
        last_day = first_day - timedelta(days=1)
        first_day = datetime(last_day.year, last_day.month, 1, tzinfo=utc)
        bmi_stats.append(tkt_group_metrics.get_bmi_monthly_stats(first_day, last_day))
        
        # get daily stat from today and 4 weeks back
        last_day = datetime(today.year, today.month, today.day, tzinfo=utc)
        first_day = last_day - timedelta(days=DAYS_BACK)
        
        backlog_history = tkt_group_metrics.get_daily_backlog_history(first_day, last_day)
        daily_backlog_chart = tkt_group_metrics.get_daily_backlog_chart(backlog_history)
        
        changeset_group_stats = ChangesetsStats(self.env, first_day, last_day)
        commits_by_date = changeset_group_stats.get_commit_by_date()
        commits_by_date_chart = changeset_group_stats.get_commit_by_date_chart(commits_by_date)
        
        data['project_bmi_stats'] = bmi_stats
        #self.env.log.info(bmi_stats)
        data['ticket_frequency_stats'] = tkt_frequency_stats
        data['ticket_duration_stats'] = tkt_duration_stats
        data['ds_daily_backlog'] = daily_backlog_chart
        data['ds_commit_by_date'] = commits_by_date_chart
        
        add_stylesheet(req, 'pd/css/dashboard.css')        
        add_stylesheet(req, 'common/css/report.css')
        
        return 'pdashboard.html', data, None
   
    # ITemplateProvider methods
    # Used to add the plugin's templates and htdocs 
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('pd', resource_filename(__name__, 'htdocs'))]    
