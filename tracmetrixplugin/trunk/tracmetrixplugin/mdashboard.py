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
import os

from bisect import bisect
from datetime import timedelta
from itertools import groupby

from pylab import date2num, drange, num2date #FIXME: use Trac's date utils and get rid of the pylab dependency.

from genshi.builder import tag
from trac.config import BoolOption, ExtensionOption, IntOption, Option
from trac.core import Component, implements, TracError
from trac.perm import IPermissionRequestor
from trac.ticket.model import Milestone, TicketSystem
from trac.ticket.roadmap import ITicketGroupStatsProvider, get_ticket_stats, get_tickets_for_milestone, milestone_stats_data
from trac.util.compat import sorted
from trac.util.datefmt import to_datetime, format_date, utc    
from trac.web import IRequestHandler
from trac.web.chrome import add_link, add_stylesheet, INavigationContributor, ITemplateProvider
from trac.wiki.api import IWikiSyntaxProvider


def get_every_tickets_in_milestone(db, milestone):
    """ Get list of ticket id that have ever been in this milestone.  
    This includes the ticket that was assigned to the milestone and 
    later reassigned to a different milestone.
    """
    cursor = db.cursor()
    
    # this sql can have ticket that is still in the milestone.
#    cursor.execute("SELECT id, status, type FROM ticket "
#                        "WHERE id IN (SELECT DISTINCT ticket FROM ticket_change "
#                        "WHERE (ticket_change.field='milestone' AND "
#                        "ticket_change.oldvalue=%s))", (milestone,))
    
    cursor.execute("SELECT id FROM ticket WHERE id IN "
                   "(SELECT DISTINCT ticket FROM ticket_change "
                   "WHERE (ticket_change.field='milestone' AND "
                   "ticket_change.oldvalue=%s)) "
                   "UNION SELECT id FROM ticket WHERE milestone=%s",
                   (milestone, milestone))  
    tickets = []
    for tkt_id, in cursor:
        tickets.append(tkt_id)  #tkt_id is a tuple of lengh 1
                
    return tickets       

def add_milestone_event(env, history, time, event, ticket_id):    
                    
    if history.has_key(time):

        history[time][event].add(ticket_id)
    else:
        
        history[time] = {'Enter':set([]), 'Leave':set([]), 'Finish':set([])}
        #make the list of ticket as set so that there is no duplicate
        #this is to handle the case where many ticket fields are changed 
        #at the same time.
        history[time][event].add(ticket_id)
                                
def collect_tickets_status_history(env, db, ticket_ids, milestone):
    
    history = {}

    cursor = db.cursor()
    
    sqlquery = "SELECT ticket.id AS tid, ticket.type, ticket.time, ticket.status, " \
               "ticket_change.time, ticket.milestone, ticket_change.field, " \
               "ticket_change.oldvalue, ticket_change.newvalue " \
               "FROM ticket LEFT JOIN ticket_change ON ticket.id = ticket_change.ticket " \
               "WHERE (ticket_change.field='status' " \
               "OR ticket_change.field='milestone') AND ticket.id IN (%s) " \
               "UNION SELECT ticket.id AS tid, ticket.type, ticket.time, ticket.status, " \
               "ticket.time, ticket.milestone, null, null, null FROM ticket " \
               "WHERE ticket.time = ticket.changetime " \
               "AND ticket.id IN (%s) ORDER BY tid" \
               % ((",".join(['%s'] * len(ticket_ids))), (",".join(['%s'] * len(ticket_ids))))
        
#    sqlquery = "SELECT ticket.id, ticket.type, ticket.time, ticket.status, " \
#                   "ticket.time as changetime, null, null, null FROM ticket " \
#                   "WHERE ticket.time = ticket.changetime " \
#                   "AND ticket.id IN (%s) ORDER BY changetime" % (ticket_list,)
#    
    cursor.execute(sqlquery, tuple(ticket_ids) + tuple(ticket_ids))
    
    #env.log.info(sqlquery)
    event_history = cursor.fetchall()
    
    #env.log.info("event_history = %s" % (event_history,))
    
    # TODO The tricky thing about this is that we have to deterimine 5 different type of ticket.
    # 1) created with milestone and remain in milestone (new and modified)
    # 2) create with milestone then later leave milestone 
    # 3) created with milestone and leave milestone and come back and remain in milestone
    # 4) create w/o milestone and later assigned to milestone and remain in the milestone
    # 5) create w/o milestone then later assigned to milestone but then later leave milestone
    # 6) Create w/o milestone and closed then later assigned to milestone
    # 7) create with different milestone then later assigned to milestone
    # Need to find the first time each ticket enters the milestone
    
    # key is the tuple (tkt_id, tkt_createdtime)    
    for ticket, events in groupby(event_history, lambda l: (l[0], l[2])):
    
        status_events = []
        # flag to determine whether the milestone has changed for the first time
        milestone_changed = False
        
        # Assume that ticket is created with out milestone.
        # The event will be store in the list until we find out what milestone do the
        # event belong to.
        current_milestone = None
        current_status = 'Active'
        for tkt_id, tkt_type, tkt_createdtime, tkt_status, tkt_changedtime, \
            tkt_milestone, tkt_field, tkt_oldvalue, tkt_newvalue in events:
                
            # If the ticket was modified
            if tkt_createdtime != tkt_changedtime:

                # Ticket that was created with out milestone
                if tkt_field == 'milestone':

                    # Ticket was created with blank milestone or other milestone
                    if tkt_newvalue == milestone.name:
                        
                        current_milestone = milestone.name
                        
                        # in case that closed ticket was assigned to the milestone
                        if current_status == 'closed':
                            add_milestone_event(env, history, tkt_changedtime, 'Enter', tkt_id)
                            add_ticket_status_event(env, history, tkt_changedtime, tkt_status, tkt_id)
                        else:
                            add_milestone_event(env, history, tkt_changedtime, 'Enter', tkt_id)
                    
                    # Ticket leave the milestone
                    elif tkt_oldvalue == milestone.name:
                        
                        current_milestone = tkt_newvalue
                        
                        # Ticket was create with milestone
                        if milestone_changed == False:
                            # update the enter event
                            add_milestone_event(env, history, tkt_createdtime, 'Enter', tkt_id)
                            # it means that the eariler status event has to be in the milestone.
                            for tkt_changedtime, tkt_newvalue, tkt_id in status_events:
                                add_ticket_status_event(env, history, tkt_changedtime, tkt_newvalue, tkt_id)
                            
                        add_milestone_event(env, history, tkt_changedtime, 'Leave', tkt_id)
                    
                    milestone_changed = True                        
                 
                elif tkt_field == 'status':
                    
                    current_status = tkt_newvalue
                    
                    # this event happen before milestone is changed
                    if milestone_changed == False:
                        
                        status_events.append((tkt_changedtime, tkt_newvalue, tkt_id))
                        
                        #env.log.info(status_events)
                    
                    else:
                        # only add ticket status that happen in the milestone
                        if current_milestone == milestone.name:
                            add_ticket_status_event(env, history, tkt_changedtime, tkt_newvalue, tkt_id)
                    
            # new ticket that was created and assigned to the milestone
            else:
                add_milestone_event(env, history, ticket[1], 'Enter', ticket[0])

        # if milestone never changed it means that the ticket was assing to the milestone.
        if milestone_changed == False:
           
            add_milestone_event(env, history, tkt_createdtime, 'Enter', tkt_id)                            
            # it means that the eariler status event has to be in the milestone.
            for tkt_changedtime, tkt_newvalue, tkt_id in status_events:
                add_ticket_status_event(env, history, tkt_changedtime, tkt_newvalue, tkt_id)

    return history

def add_ticket_status_event(env, history, time, status, tkt_id):
    
    # ticket was closed                
    if status == 'closed':
        add_milestone_event(env, history, time, 'Finish', tkt_id)
                
    # ticket was reopened
    elif status == 'reopened':
        add_milestone_event(env, history, time, 'Enter', tkt_id)


def make_ticket_history_table(env, dates, sorted_events):
    """
        This function takes list of dates in milestone and ticket events
        then produce a dictionary with key as milestone event and value as 
        that list of ticket counts each day.
        
        dates is the numerical array of date in UTC time.
        sorted_event is dictionary of events that occurs in milestone
    
    """
    #Initialize the count using key in events
    
    tkt_counts = {'Enter':[], 'Leave':[], 'Finish':[]}
    
    #initialize the table    
    for date in dates:
        
        #env.log.info("Date:%s" % (num2date(date),))
        for key in tkt_counts:
            tkt_counts[key].append(0)

    #Create dictionary of list that hold ticket count each day in dates
    for event in sorted_events:
        
        #Time in epoch time
        date = to_datetime(event[0])
        
        #Get the index of this date in the dates list
        index = bisect(dates, date2num(date)) - 1
        
        for key in tkt_counts:
            tkt_counts[key][index] = tkt_counts[key][index] + len(event[1][key])
         
    return tkt_counts
    
    
    
def make_cumulative_data(env, tkt_counts):
     
    #create cumulative ticket count list
    
    tkt_cumulative = {}
    
    # initialize by assigning the first data point of 
    # each data set in tkt_counts to tkt_cumulative
   
    for key in tkt_counts:
        
        tkt_cumulative[key] = []
                
        for index, num_ticket in enumerate(tkt_counts[key]):
            if index == 0:
                next_value = tkt_counts[key][index]                
            else:
                next_value = tkt_cumulative[key][index - 1] + tkt_counts[key][index]
            
            tkt_cumulative[key].append(next_value)
 
#    for event in tkt_cumulative:
#        env.log.info(tkt_cumulative[event])            
    return tkt_cumulative

class MDashboard(Component):

    implements(INavigationContributor, IPermissionRequestor, IRequestHandler,
               IWikiSyntaxProvider, ITemplateProvider, ITicketGroupStatsProvider)
 
    yui_base_url = Option('pdashboard', 'yui_base_url',
                          default='http://yui.yahooapis.com/2.7.0',
                          doc='Location of YUI API')
 
    stats_provider = ExtensionOption('mdashboard', 'stats_provider',
                                     ITicketGroupStatsProvider,
                                     'ProgressTicketGroupStatsProvider',
        """Name of the component implementing `ITicketGroupStatsProvider`, 
        which is used to collect statistics on groups of tickets for display
        in the milestone views.""")
    
    tickettype_stats_provider = ExtensionOption('mdashboard', 'tickettype_stats_provider',
                                     ITicketGroupStatsProvider,
                                     'TicketTypeGroupStatsProvider',
        """Name of the component implementing `ITicketGroupStatsProvider`, 
        which is used to collect statistics on groups of tickets for display
        in the milestone views.""")
    
    default_daysback = IntOption('mdashboard', 'default_daysback', 30,
        """Default number of days displayed in the Timeline, in days.
        (''since 0.9.'')""")
    
    abbreviated_messages = BoolOption('mdashboard', 'abbreviated_messages',
                                      'true',
        """Whether wiki-formatted event messages should be truncated or not.

        This only affects the default rendering, and can be overriden by
        specific event providers, see their own documentation.
        (''Since 0.11'')""")
    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'pdashboard'

    def get_navigation_items(self, req):
        return []
    # IPermissionRequestor methods

    def get_permission_actions(self):
        actions = ['MILESTONE_CREATE', 'MILESTONE_DELETE', 'MILESTONE_MODIFY',
                   'MILESTONE_VIEW']
        return actions + [('MILESTONE_ADMIN', actions),
                          ('ROADMAP_ADMIN', actions)]

    # IRequestHandler methods

    def match_request(self, req):

        self.env.log.info("mdashboard match request %s" % (req.path_info,))  

        match = re.match(r'/mdashboard(?:/(.+))?', req.path_info)
               
        if match:
            if match.group(1):
                req.args['id'] = match.group(1)
            return True
        # This code should do what above does.
        #req.path_info.startswith('/mdashboard')


    def process_request(self, req):
        
        req.perm.require('MILESTONE_VIEW')
        
        milestone_id = req.args.get('id')

        self.env.log.info("mdashboard process request %s, %s" % (req.path_info, req.args.get('id')))  

        add_link(req, 'up', req.href.pdashboard(), 'Dashboard')

        db = self.env.get_db_cnx()
        milestone = Milestone(self.env, milestone_id, db)

        if not milestone_id:
            req.redirect(req.href.pdashboard())     
                       
        self.env.log.info("request mdashboard")
        add_stylesheet(req, 'pd/css/dashboard.css')  
        
        return self._render_view(req, db, milestone)        
        

    def _render_view(self, req, db, milestone):
        milestone_groups = []
        available_groups = []
        component_group_available = False
        ticket_fields = TicketSystem(self.env).get_ticket_fields()

        # collect fields that can be used for grouping
        for field in ticket_fields:
            if field['type'] == 'select' and field['name'] != 'milestone' \
                    or field['name'] in ('owner', 'reporter'):
                available_groups.append({'name': field['name'],
                                         'label': field['label']})
                if field['name'] == 'component':
                    component_group_available = True

        # determine the field currently used for grouping
        by = None
        if component_group_available:
            by = 'component'
        elif available_groups:
            by = available_groups[0]['name']
        by = req.args.get('by', by)

        tickets = get_tickets_for_milestone(self.env, db, milestone.name, by)
        stat = get_ticket_stats(self.stats_provider, tickets)
        tstat = get_ticket_stats(self.tickettype_stats_provider, tickets)
                
        # Parse the from date and adjust the timestamp to the last second of
        # the day
        today = to_datetime(None, req.tz)

        # Get milestone start date from session or use default day back.
        # TODO: add logic to remember the start date either in db or session.
#        if  req.session.get('mdashboard.fromdate') != None:
#
#            fromdate = parse_date(req.session.get('mdashboard.fromdate'), req.tz)        
#        else: 
        fromdate = today - timedelta(days=self.default_daysback + 1)
        fromdate = fromdate.replace(hour=23, minute=59, second=59)

        # Data for milestone and timeline
        data = {'fromdate': fromdate,
                'milestone': milestone,
                'tickethistory' : [],
                'dates' : [],
                'ticketstat' : {},
                'yui_base_url': self.yui_base_url 
                }
            
        data.update(milestone_stats_data(self.env, req, stat, milestone.name))
        
        ticketstat = {'name':'ticket type'}
        ticketstat.update(milestone_stats_data(self.env, req, tstat, milestone.name))
        data['ticketstat'] = ticketstat
        
        #self.env.log.info("ticketstat = %s" % (ticketstat,))
        
        # get list of ticket ids that in the milestone
        #ctickets = get_tickets_for_milestone(self.env, db, milestone.name, 'type')
        everytickets = get_every_tickets_in_milestone(db, milestone.name)
        
        if everytickets != []:
        
            #tkt_history = {}
            
#            collect_tickets_status_history(self.env, db, tkt_history, \
#                                           everytickets, milestone)
            
            tkt_history = collect_tickets_status_history(self.env, db, everytickets, milestone)
            
            if tkt_history != {}:
                            
                # Sort the key in the history list
                # returns sorted list of tuple of (key, value)
                sorted_events = sorted(tkt_history.items(), key=lambda(k, v):(k))
        
                #debug  
                self.env.log.info("sorted_event content")
                for event in sorted_events:
                    self.env.log.info("date: %s: event: %s" % (format_date(to_datetime(event[0])), event[1]))
        
              
                # Get first date that ticket enter the milestone
                min_time = min(sorted_events)[0] #in Epoch Seconds
                begin_date = to_datetime(min_time).date()
                end_date = milestone.completed or to_datetime(None).date()
            
                # this is array of date in numpy
                numdates = drange(begin_date, end_date + timedelta(days=1), timedelta(days=1))
                
                tkt_history_table = make_ticket_history_table(self.env, numdates, sorted_events)
        
                #debug
                #self.env.log.info("tkt_history_table: %s", (tkt_history_table,))   
                
                #Create a data for the cumulative flow chart.
                tkt_cumulative_table = make_cumulative_data(self.env, tkt_history_table)
                
                #debug
                #self.env.log.info(tkt_cumulative_table)   
            
                # creat list of dateobject from dates
                dates = []
                for numdate in numdates:
                    
                    utc_date = num2date(numdate)
                    dates.append(utc_date)
                    #self.env.log.info("%s: %s" % (utc_date, format_date(utc_date, tzinfo=utc)))
                
                    #prepare Yahoo datasource for comulative flow chart
                dscumulative = ''
                for idx, date in enumerate(dates):
                    dscumulative = dscumulative + '{ date: "%s", enter: %d, leave: %d, finish: %d}, ' \
                          % (format_date(date, tzinfo=utc), tkt_cumulative_table['Enter'][idx], \
                             tkt_cumulative_table['Leave'][idx], tkt_cumulative_table['Finish'][idx])
  
                
                
                data['tickethistory'] = tkt_cumulative_table
                data['dates'] = dates
                data['dscumulative'] = '[ ' + dscumulative + ' ];'
                
        return 'mdashboard.html', data, None
   
    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        return []

    def get_link_resolvers(self):
        yield ('mdashboard', self._format_link)

    def _format_link(self, formatter, ns, name, label):
        name, query, fragment = formatter.split_link(name)
        href = formatter.href.mdashboard(name) + query + fragment
        try:
            milestone = Milestone(self.env, name, formatter.db)
        except TracError:
            milestone = Milestone(self.env)
        # Note: this should really not be needed, exists should simply be false
        # if the milestone doesn't exist in the db
        if milestone.exists:
            closed = milestone.completed and 'closed ' or ''
            return tag.a(label, class_='%smilestone' % closed, href=href)
        else: 
            return tag.a(label, class_='missing milestone', href=href,
                         rel="nofollow")

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

