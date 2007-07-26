# -*- coding: utf-8 -*-
#
# Copyright (C) 2007      Bhuricha Sethanandha
# All rights reserved.
#
#
# Author: Bhuricha Sethanandha <khundeen@gmail.com>
import re
from genshi.builder import tag
from trac import __version__
from trac import mimeview

from trac.config import ExtensionOption
from trac.context import Context
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.ticket import Milestone, Ticket, model #These are object
from trac.ticket.query import Query
from trac.ticket.roadmap import ITicketGroupStatsProvider, DefaultTicketGroupStatsProvider, \
                                get_ticket_stats, get_tickets_for_milestone, \
                                milestone_stats_data, TicketGroupStats
from trac.util.compat import sorted
from trac.web import IRequestHandler, IRequestFilter
from trac.web.chrome import add_stylesheet, INavigationContributor, ITemplateProvider

class ProgressTicketGroupStatsProvider(Component):
    implements(ITicketGroupStatsProvider)

    def get_ticket_group_stats(self, ticket_ids):
        
        # ticket_ids is a list of ticket id as number.
        total_cnt = len(ticket_ids)
        if total_cnt:
            cursor = self.env.get_db_cnx().cursor() # get database connection
            str_ids = [str(x) for x in sorted(ticket_ids)] # create list of ticket id as string
            
            
            closed_cnt = cursor.execute("SELECT count(1) FROM ticket "
                                        "WHERE status = 'closed' AND id IN "
                                        "(%s)" % ",".join(str_ids)) # execute query and get cursor obj.
            closed_cnt = 0
            for cnt, in cursor:
                closed_cnt = cnt
                
            active_cnt = cursor.execute("SELECT count(1) FROM ticket "
                                        "WHERE status IN ('new', 'reopened') "
                                        "AND id IN (%s)" % ",".join(str_ids)) # execute query and get cursor obj.
            active_cnt = 0
            for cnt, in cursor:
                active_cnt = cnt
                
        else:
            closed_cnt = 0
            active_cnt = 0

        inprogress_cnt = total_cnt - ( active_cnt + closed_cnt)

        stat = TicketGroupStats('ticket status', 'ticket')
        stat.add_interval('closed', closed_cnt,
                          {'status': 'closed', 'group': 'resolution'},
                          'closed', True)
        stat.add_interval('inprogress', inprogress_cnt,
                          {'status': ['accepted', 'assigned']},
                          'inprogress', False)
        stat.add_interval('new', active_cnt,
                          {'status': ['new', 'reopened']},
                          'new', False)
                          
        stat.refresh_calcs()
        return stat


class TicketTypeGroupStatsProvider(Component):
    implements(ITicketGroupStatsProvider)

    def get_ticket_group_stats(self, ticket_ids):
        
        # ticket_ids is a list of ticket id as number.
        total_cnt = len(ticket_ids)
        if total_cnt:
            str_ids = [str(x) for x in sorted(ticket_ids)] # create list of ticket id as string
            cursor = self.env.get_db_cnx().cursor()  # get database connection    
            
            type_count = [] # list of dictionary with key name and count
            
            for type in model.Type.select(self.env):
            
                count = cursor.execute("SELECT count(1) FROM ticket "
                                        "WHERE type = '%s' AND id IN "
                                        "(%s)" % (type.name, ",".join(str_ids))) # execute query and get cursor obj.
                count = 0
                for cnt, in cursor:
                    count = cnt

                if count > 0:
                    type_count.append({'name':type.name,'count':count})

        
        stat = TicketGroupStats('ticket type', 'ticket')
        
        for type in type_count:
                
            if type['name'] != 'defect': # default ticket type 'defect'
        
                stat.add_interval(type['name'], type['count'],
                                  {'type': type['name']}, 'value', True)
            
            else:
                stat.add_interval(type['name'], type['count'],
                                  {'type': type['name']}, 'waste', False)
                          
        stat.refresh_calcs()
        return stat

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
                
        return re.match(r'/pdashboard/?', req.path_info) is not None

    def process_request(self, req):
        req.perm.require('ROADMAP_VIEW')

        showall = req.args.get('show') == 'all'

        db = self.env.get_db_cnx()
        
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
            'context': Context(self.env, req),
            'milestones': milestones,
            'milestone_stats': stats,
            'queries': queries,
            'showall': showall,
            'project' : project
        }
        
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
