# -*- coding: utf-8 -*-
#
# Copyright (C) 2007      Bhuricha Sethanandha
# All rights reserved.
#
#
# Author: Bhuricha Sethanandha <khundeen@gmail.com>
import re
import os

from string import find
from bisect import bisect
from itertools import groupby
from datetime import datetime, timedelta, date
import re
from time import localtime, strftime, time, mktime

from genshi.builder import tag

#from pylab import drange, array, searchsorted, date2num, num2date, \
#                  plot, savefig, axis, xlabel, ylable, title, legend
import matplotlib
from pylab import *
from matplotlib.dates import DayLocator, HourLocator, DateFormatter, drange

from trac import __version__
from trac import mimeview
from trac.core import *
from trac.context import Context
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.util import sorted
from trac.util.compat import sorted
from trac.util.datefmt import parse_date, utc, to_timestamp, to_datetime, \
                              get_date_format_hint, get_datetime_format_hint, \
                              format_date, format_datetime, pretty_timedelta
from trac.util.text import shorten_line, CRLF, to_unicode
from trac.ticket import Milestone, Ticket, TicketSystem #These are object
from trac.ticket.query import Query
from trac.ticket.roadmap import ITicketGroupStatsProvider, DefaultTicketGroupStatsProvider, \
                                get_ticket_stats, get_tickets_for_milestone, \
                                milestone_stats_data, TicketGroupStats
from trac.timeline.api import ITimelineEventProvider, TimelineEvent
from trac.web import IRequestHandler, IRequestFilter
from trac.web.chrome import add_link, add_stylesheet, INavigationContributor, ITemplateProvider
from trac.wiki.api import IWikiSyntaxProvider
from trac.config import ExtensionOption, IntOption, BoolOption


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

def add_milestone_event(history, time, event, ticket_id):
    
    if history.has_key(time):

        history[time][event].add(ticket_id)
    else:
        
        history[time]={'Enter':set([]), 'Leave':set([]), 'Finish':set([])}
        #make the list of ticket as set so that there is no duplicate
        #this is to handle the case where many ticket fields are changed 
        #at the same time.
        history[time][event].add(ticket_id)

def collect_tickets_status_history(env, db, history, ticket_ids, milestone):

    cursor = db.cursor()
    str_ids = [str(x) for x in sorted(ticket_ids)]
    ticket_list = ",".join(str_ids)
    
    sqlquery = "SELECT ticket.id, ticket.type, ticket.time, ticket.status, " \
                       "ticket_change.time, ticket.milestone, ticket_change.field, " \
                       "ticket_change.oldvalue, ticket_change.newvalue " \
                       "FROM ticket LEFT JOIN ticket_change ON ticket.id = ticket_change.ticket " \
                       "WHERE (ticket_change.field='status' " \
                       "OR ticket_change.field='milestone') AND ticket.id IN (%s) " \
                       "UNION SELECT ticket.id, ticket.type, ticket.time, ticket.status, " \
                       "ticket.time, ticket.milestone, null, null, null FROM ticket " \
                       "WHERE ticket.time = ticket.changetime " \
                       "AND ticket.id IN (%s) ORDER BY ticket.id" % (ticket_list, ticket_list)
        
#    sqlquery = "SELECT ticket.id, ticket.type, ticket.time, ticket.status, " \
#                   "ticket.time as changetime, null, null, null FROM ticket " \
#                   "WHERE ticket.time = ticket.changetime " \
#                   "AND ticket.id IN (%s) ORDER BY changetime" % (ticket_list,)
#    
    cursor.execute(sqlquery)
    
    env.log.info(sqlquery)
    event_history = cursor.fetchall()
    
    #env.log.info("event_history = %s" % (event_history,))
    
    # TODO The tricky thing about this is that we have to deterimine 5 different type of ticket.
    # 1) created with milestone and remain in milestone (new and modified)
    # 2) create w/o milestone and later assigned to milestone and remain in the milestone
    # 3) create with milestone then later leave milestone
    # 4) create w/o milestone then later assigned to milestone but then later leave milestone
    # 5) created with milestone and leave milestone and come back and remain in milestone
    # Need to find the first time each ticket enters the milestone
    
    # key is the tuple (tkt_id, tkt_createdtime)    
    for ticket, events in groupby(event_history, lambda l: (l[0], l[2])):
    
        # assume that ticket assigned milestone when created.
        add_milestone_event(history, ticket[1], 'Enter', ticket[0])
        
        # flag to deterimine when milestone is changed for the first time
        first_milestone = True
    
        for tkt_id, tkt_type, tkt_createdtime, tkt_status, tkt_changedtime, \
            tkt_milestone, tkt_field, tkt_oldvalue, tkt_newvalue in events:
                
            # If the ticket was modified
            if tkt_createdtime != tkt_changedtime:

                # Ticket that was created with out milestone
                if tkt_field == 'milestone':
                    
                    if tkt_newvalue == milestone.name:
                        
                        # means that ticket was moved to this milestone
                        # adjust the enter date accordingly
                        if first_milestone == True:
                            history[tkt_createdtime]['Enter'].remove(tkt_id)              
                            
                            # remove the key if nothing is in there
                            if (len(history[tkt_createdtime]['Enter']) == 0 and \
                                len(history[tkt_createdtime]['Leave']) == 0 and \
                                len(history[tkt_createdtime]['Finish']) == 0 ):
                                history.pop(tkt_createdtime)                                
                            
                            add_milestone_event(history, tkt_changedtime, 'Enter', tkt_id)
                            first_milestone = False
                            
                        # means that ticket was assigned back to the milestone again
                        elif first_milestone == False:
                            add_milestone_event(history, tkt_changedtime, 'Enter', tkt_id)
                
                    # ticket was rescheduled to different milestone
                    elif tkt_oldvalue == milestone.name:
                        add_milestone_event(history, tkt_changedtime, 'Leave', tkt_id)
                
                elif tkt_field == 'status':
                    # ticket was closed                
                    if tkt_newvalue == 'closed':
                        add_milestone_event(history, tkt_changedtime, 'Finish', tkt_id)
                
                    # ticket was reopened
                    elif tkt_newvalue == 'reopened':
                        add_milestone_event(history, tkt_changedtime, 'Enter', tkt_id)
                        

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
        
        env.log.info("Date:%s" % (num2date(date),))
        for key in tkt_counts:
            tkt_counts[key].append(0)

    #Create dictionary of list that hold ticket count each day in dates
    for event in sorted_events:
        
        #Time in epoch time
        date = datetime.fromtimestamp(event[0], utc).date()
        
        env.log.info("Event Date:%s:%s" % (date,event[1]))
        
        #get index of day in the dates list
        index = bisect(dates, date2num(date)) - 1
        
        for key in tkt_counts:
            tkt_counts[key][index] = tkt_counts[key][index] + len(event[1][key])
         
    return tkt_counts
    
    
    
def make_cummulative_data(env, tkt_counts):
     
    #create cummulative ticket count list
    
    tkt_cummulative = {}
    
    # initialize by assigning the first data point of 
    # each data set in tkt_counts to tkt_cummulative
   
    for key in tkt_counts:
        
        tkt_cummulative[key] = []
                
        for index, num_ticket in enumerate(tkt_counts[key]):
            if index == 0:
                next_value = tkt_counts[key][index]                
            else:
                next_value = tkt_cummulative[key][index-1] + tkt_counts[key][index]
            
            tkt_cummulative[key].append(next_value)
 
    for event in tkt_cummulative:
        env.log.info(tkt_cummulative[event])            
 
    return tkt_cummulative

def create_cummulative_chart(env, milestone, numdates, tkt_cummulative_table): 
    
    matplotlib.use('Agg')
    cla()
    fig = figure()
    ax = fig.add_subplot(111) # Create supplot with key 111       
    ax.plot(numdates, tkt_cummulative_table['Enter'], 'b-')
    ax.plot(numdates, tkt_cummulative_table['Leave'], 'r-') 
    ax.plot(numdates, tkt_cummulative_table['Finish'], 'g-')
    ax.set_xlim( numdates[0], numdates[-1] )
    ax.xaxis.set_major_locator(DayLocator())
    ax.xaxis.set_major_formatter( DateFormatter('%Y-%m-%d'))
    ax.fmt_xdata = DateFormatter('%Y-%m-%d %H:%M:%S')
    labels = ax.get_xticklabels()
    setp(labels, rotation=45, fontsize=8)
    
    xlabel('Dates (day)')
    ylabel('Counts (times)')
    title('Cummulative flow chart for ticket status history')
    legend(('Ticket Entered', 'Ticket Left', 'Ticket Completed'), loc='upper left')
    
    filename = "cummulativeflow_%s" % (milestone.name,)
    path = os.path.join(env.path, 'cache', 'tracmetrixplugin', filename)
    env.log.info(path)  
    
    fig.savefig(path)
    
    return path
   
class MDashboard(Component):

    implements(INavigationContributor, IPermissionRequestor, IRequestHandler,
               IWikiSyntaxProvider, ITemplateProvider, ITicketGroupStatsProvider)
 
    stats_provider = ExtensionOption('mdashboard', 'stats_provider',
                                     ITicketGroupStatsProvider,
                                     'ProgressTicketGroupStatsProvider',
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
        import re, urllib

        self.env.log.info("mdashboard match request %s" % (req.path_info,))  

        match = re.match(r'/mdashboard(?:/(.+))?', req.path_info)
               
        if match:
            if match.group(1):
                
                # split the milestone name.  This part can be 'milestone name' or 
                # 'milestone name/image name'
                
                urlcomp = match.group(1).split('/')
                
                if len(urlcomp) == 1: #url has 2 
                    req.args['id'] = urlcomp[0]
                    req.args['imagename'] = None
                else:
                    req.args['id'] = urlcomp[0]
                    req.args['imagename'] = urlcomp[1]
                    
            return True
        # This code should do what above does.
        #req.path_info.startswith('/mdashboard')


    def process_request(self, req):
        
        req.perm.require('MILESTONE_VIEW')
        
        milestone_id = req.args.get('id')

        self.env.log.info("mdashboard process request %s, %s" % (req.path_info,req.args.get('id')))  

        add_link(req, 'up', req.href.pdashboard(), 'Dashboard')

        db = self.env.get_db_cnx()
        milestone = Milestone(self.env, milestone_id, db)

        if not milestone_id:
            req.redirect(req.href.pdashboard())     
            
        if req.args.get('imagename') == 'cummulativeflow.png':    
            
            self.env.log.info("request for image")
            filename = "cummulativeflow_%s.png" % (milestone.name,)
            path = os.path.join(self.env.path, 'cache', 'tracmetrixplugin', filename)
            req.send_file(path, mimeview.get_mimetype(path))
            
        else:
            
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
                
        # get list of ticket ids that in the milestone
        #ctickets = get_tickets_for_milestone(self.env, db, milestone.name, 'type')
        everytickets = get_every_tickets_in_milestone(db, milestone.name)
        
        # Parse the from date and adjust the timestamp to the last second of
        # the day
        today = datetime.now(req.tz)

        # Get milestone start date from session or use default day back.
        # TODO: add logic to remember the start date either in db or session.
#        if  req.session.get('mdashboard.fromdate') != None:
#
#            fromdate = parse_date(req.session.get('mdashboard.fromdate'), req.tz)        
#        else: 
        fromdate = today - timedelta(days=self.default_daysback + 1)
 
        #precisedate is in datetime type.
        precisedate = precision = None
        
        # When the update button is clicked.
        if 'from' in req.args:            
            precisedate = parse_date(req.args.get('from'), req.tz)
            fromdate = precisedate
            precision = req.args.get('precision', '')
            if precision.startswith('second'):
                precision = timedelta(seconds=1)
            elif precision.startswith('minutes'):
                precision = timedelta(minutes=1)
            elif precision.startswith('hours'):
                precision = timedelta(hours=1)
            else:
                precision = None

        fromdate = fromdate.replace(hour=23, minute=59, second=59)
                
        # TODO: Create the data structure to store the history table.
        # This can either be list of dict or dict of dict.  
        tkt_history = {}
        
        collect_tickets_status_history(self.env, db, tkt_history, \
                                       everytickets, milestone)
                        
        # Sort the key in the history list
        # returns sorted list of tuple of (key, value)
        sorted_events = sorted(tkt_history.items(), key=lambda(k,v):(k))

        #debug  
        for event in sorted_events:
            self.env.log.info("date: %s: event: %s" % (format_date(to_datetime(event[0])), event[1]))

      
        # Get first date that ticket enter the milestone
        min_time = min(sorted_events)[0] #in Epoch Seconds
        begin_date = datetime.fromtimestamp(min_time, utc).date() 
        
        if milestone.completed != None:
            end_date = milestone.completed        
        else:
            end_date = datetime.now(utc).date()
        
        self.env.log.info("begindate: Timezone %s:%s, UTC:%s)" % \
                          (req.tz,datetime.fromtimestamp(min_time, req.tz).date(), \
                           datetime.fromtimestamp(min_time, utc).date())) 

        self.env.log.info("enddate: UTC:%s" % (end_date,))
        
        # Data for milestone and timeline
        data = {'fromdate': fromdate,
                'milestone': milestone,
                'begindate' : begin_date,
                'enddate' : end_date,
                'tickethistory' : [],
                'dates' : []}
        
        data.update(milestone_stats_data(req, stat, milestone.name))
        
    
        # this is array of date in numpy
        numdates = drange(begin_date, end_date + timedelta(days=1), timedelta(days=1))
        
        tkt_history_table = make_ticket_history_table(self.env, numdates, sorted_events)

        #debug
        self.env.log.info("tkt_history_table: %s", (tkt_history_table,))   
        
        #Create a data for the cumulative flow chart.
        tkt_cummulative_table = make_cummulative_data(self.env, tkt_history_table)
        
        #debug
        self.env.log.info(tkt_cummulative_table)   
    
        # creat list of dateobject from dates
        dates = []
        for numdate in numdates:
            
            utc_date = num2date(numdate)
            dates.append(utc_date)
            self.env.log.info("%s: %s" % (utc_date, format_date(utc_date, tzinfo=utc)))
                              
        
        data['tickethistory'] = tkt_cummulative_table
        data['dates'] = dates
        
        create_cummulative_chart(self.env, milestone, numdates, tkt_cummulative_table)

        
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

