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

from datetime import timedelta, datetime

from genshi.builder import tag
from genshi.filters.transform import StreamBuffer, Transformer
from trac.config import ExtensionOption, Option
from trac.core import Component, implements
from trac.mimeview import Context
from trac.perm import IPermissionRequestor
from trac.ticket.model import Milestone
from trac.ticket.query import Query
from trac.ticket.roadmap import (
    ITicketGroupStatsProvider, get_ticket_stats,
    get_tickets_for_milestone, milestone_stats_data
)
from trac.util.datefmt import to_datetime, utc
from trac.web.api import IRequestFilter, IRequestHandler, ITemplateStreamFilter
from trac.web.chrome import (
    INavigationContributor, ITemplateProvider, add_stylesheet
)

from tracmetrixplugin.model import ChangesetsStats, TicketGroupMetrics

# Constants
DAYS_BACK = 28

def last_day_of_month(year, month):

    # For december the next month will be january of next year.
    if month == 12:
 	year = year + 1

    return datetime(year + (month / 12), (month % 12) + 1 , 1, tzinfo=utc) - timedelta(days=1)

class GenerateMetrixLink(object):

    """
    Takes a C{StreamBuffer} object containing a milestone name and creates a
    hyperlink to the TracMetrixPlugin dashboard page for that milestone.
    See: http://groups.google.com/group/genshi/msg/3193e468b6b52395
    """

    def __init__(self, buffer, baseHref):
        """
        @param buffer: An C{StreamBuffer} instance containing the name of a milestone
        @param baseHref: An C{trac.web.href.Href} instance that is aware of
        TracMetrixPlugin navigation plugins.
        """
        self.buffer = buffer
        self.baseHref = baseHref

    def __iter__(self):

        """
        Return a <dd><a> link to be inserted at the end of the stats block of
        the milstone summary.
        """
        milestoneName = u"".join(e[1] for e in self.buffer.events)
        title = "Go to TracMetrix for %s" % milestoneName
        href = self.baseHref.mdashboard(milestoneName)

        return iter(tag.dd('[', tag.a('TracMetrix', href=href, title=title), ']'))



class RoadmapMetrixIntegrator(Component):

    """
    Add a link from each milestone in the roadmap, to the corresponding
    metrix dashboard page.
    """
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):

        if filename in ('roadmap.html',):

            buffer = StreamBuffer()
            t = Transformer('//li[@class="milestone"]/div[@class="info"]/h2/a/em/text()')
            t = t.copy(buffer).end()
            t = t.select('//li[@class="milestone"]/div[@class="info"]/dl')
            t = t.append(GenerateMetrixLink(buffer, req.href))
            stream |= t

        return stream

class MilestoneMetrixIntegrator(Component):

    """Add a link from the milestone view, to the corresponding metrix
    dashboard page.
    """
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):

        if filename in ('milestone_view.html',):

            buffer = StreamBuffer()
            t = Transformer('//div[@class="milestone"]/h1/text()[2]')
            t = t.copy(buffer).end()
            t = t.select('//div[@class="milestone"]/div[@class="info"]/dl')
            t = t.append(GenerateMetrixLink(buffer, req.href))
            stream |= t

        return stream

class PDashboard(Component):

    implements(INavigationContributor, IPermissionRequestor, IRequestHandler, ITemplateProvider)

    yui_base_url = Option('pdashboard', 'yui_base_url',
                          default='http://yui.yahooapis.com/2.7.0',
                          doc='Location of YUI API')

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
                   tag.a('Metrics', href=req.href.pdashboard()))

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['ROADMAP_VIEW']

    # IRequestHandler methods


    def match_request(self, req):

        self.env.log.info("pdashboard match request %s" % (req.path_info,))

        return req.path_info == '/pdashboard'

    def process_request(self, req):
        req.perm.require('ROADMAP_VIEW')

        db = self.env.get_db_cnx()

        return self._render_view(req, db)


    def _render_view(self, req, db):

        showall = req.args.get('show') == 'all'
        showmetrics = req.args.get('showmetrics') == 'true'

        # Get list of milestone object for the project
        milestones = list(Milestone.select(self.env, showall, db))
        stats = []
        queries = []

        self.env.log.info("getting milestones statistics")
        for milestone in milestones:
            tickets = get_tickets_for_milestone(self.env, db, milestone.name,
                                                'owner')
            stat = get_ticket_stats(self.stats_provider, tickets)
            stats.append(milestone_stats_data(self.env, req, stat, milestone.name))

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
            'showmetrics': showmetrics,
            'project' : project,
            'yui_base_url': self.yui_base_url
        }

        self.env.log.info("getting project statistics")

        # Get project progress stats
        query = Query.from_string(self.env, 'max=0&order=id')
        tickets = query.execute(req)
        proj_stat = get_ticket_stats(self.stats_provider, tickets)

        data['proj_progress_stat'] = {'stats': proj_stat,
                                      'stats_href': req.href.query(proj_stat.qry_args),
                                      'interval_hrefs': [req.href.query(interval['qry_args'])
                                                         for interval in proj_stat.intervals]}

        ticket_ids = [t['id'] for t in tickets]
        closed_stat = self.stats_provider.get_ticket_resolution_group_stats(ticket_ids)

        data['proj_closed_stat'] = {
            'stats': closed_stat,
            'stats_href': req.href.query(closed_stat.qry_args),
            'interval_hrefs': [req.href.query(interval['qry_args'])
            for interval in closed_stat.intervals]
        }

        tkt_frequency_stats = {}
        tkt_duration_stats = {}
        bmi_stats = []
        daily_backlog_chart = {}
        today = to_datetime(None)

        if showmetrics:
            self.env.log.info("getting ticket metrics")
            tkt_group_metrics = TicketGroupMetrics(self.env, ticket_ids)

            tkt_frequency_stats = tkt_group_metrics.get_frequency_metrics_stats()
            tkt_duration_stats = tkt_group_metrics.get_duration_metrics_stats()

            #stat for this month
            first_day = datetime(today.year, today.month, 1, tzinfo=utc)
            last_day = last_day_of_month(today.year, today.month)
            bmi_stats.append(tkt_group_metrics.get_bmi_monthly_stats(first_day, last_day))

            # stat for last month        
            last_day = first_day - timedelta(days=1)
            first_day = datetime(last_day.year, last_day.month, 1, tzinfo=utc)
            bmi_stats.append(tkt_group_metrics.get_bmi_monthly_stats(first_day, last_day))

            # get daily backlog history
            last_day = datetime(today.year, today.month, today.day, tzinfo=utc)
            first_day = last_day - timedelta(days=DAYS_BACK)
            self.env.log.info("getting backlog history")
            backlog_history = tkt_group_metrics.get_daily_backlog_history(first_day, last_day)
            daily_backlog_chart = tkt_group_metrics.get_daily_backlog_chart(backlog_history)

        # Get dialy commits history
        last_day = datetime(today.year, today.month, today.day, tzinfo=utc)
        first_day = last_day - timedelta(days=DAYS_BACK)
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

        return ('pdashboard.html', data, None)

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
