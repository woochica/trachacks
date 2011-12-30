import re
import time
from datetime import timedelta, datetime
from operator import itemgetter, attrgetter

from trac.util.datefmt import format_date, utc
from trac.util.html import Markup
from trac.util.text import javascript_quote
from trac.wiki.macros import WikiMacroBase
from trac.web.chrome import Chrome
import copy
from trac.ticket.query import Query

from trac.config import IntOption, Option, ExtensionOption
from trac.core import implements, Component, TracError, Interface
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from pkg_resources import resource_filename

from trac.wiki.api import parse_args

# TracPM masks implementation details of how various plugins implement
# dates and ticket relationships and business rules about what the
# default estimate for a ticket is, etc.
#
# It provides utility functions to augment TicketQuery so that you can
# find all the descendants of a ticket (root=id) or all the tickets
# required for a specified ticket (goal=id).
#
# After querying, TracPM can be used to post-process the query results
# to augment the tickets in memory with normalized meta-data about
# their relationships.  After that processing, a ticket may have the
# properties listed below.  Which properties are present depends on
# what is configured in the [TracPM] section of trac.ini.
#
#  parent - accessed with TracPM.parent(t)
#  children - accessed with TracPM.children(t)
#
#  successors - accessed with TracPM.successors(t)
#  predecessors - accessed with TracPM.predecessors(t)
#
#  start - accessed with TracPM.start(t)
#  finish - accessed with TracPM.finish(t)
#
# FIXME - do we need access methods for estimate and worked?

class ITaskScheduler(Interface):
    # Schedule each the ticket in tickets with consideration for
    # dependencies, estimated work, hours per day, etc.
    # 
    # Assumes tickets is a list, each element contains at least the
    # fields returned by queryFields() and the whole list was
    # processed by postQuery().
    #
    # On exit, each ticket has t['calc_start'] and t['calc_finish']
    # set and can be accessed with TracPM.start() and finish().  No
    # other changes are made.  (FIXME - we should probably be able to
    # configure those field names.)
    def scheduleTasks(self, options, tickets):
        """Called to schedule tasks"""


class TracPM(Component):
    cfgSection = 'TracPM'
    fields = None

    Option(cfgSection, 'hours_per_estimate', '1', 
           """Hours represented by each unit of estimated work""")
    Option(cfgSection, 'default_estimate', '4.0', 
           """Default work for an unestimated task, same units as estimate""")
    Option(cfgSection, 'estimate_pad', '0.0', 
           """How much work may be remaining when a task goes over estimate, same units as estimate""")

    Option(cfgSection, 'fields.percent', None,
           """Ticket field to use as the data source for the percent 
              complete column.""")
    Option(cfgSection, 'fields.estimate', None, 
           """Ticket field to use as the data source for estimated work""")
    Option(cfgSection, 'fields.worked', None,
           """Ticket field to use as the data source for completed work""")
    Option(cfgSection, 'fields.start', None, 
           """Ticket field to use as the data source for start date""")
    Option(cfgSection, 'fields.finish', None, 
           """Ticket field to use as the data source for finish date""" )
    Option(cfgSection, 'fields.pred', None,
           """Ticket field to use as the data source for predecessor list""")
    Option(cfgSection, 'fields.succ', None,
           """Ticket field to use as the data source for successor list""")
    Option(cfgSection, 'fields.parent', None,
           """Ticket field to use as the data source for the parent""")

    Option(cfgSection, 'parent_format', '%s',
           """Format of ticket IDs in parent field""")
    Option(cfgSection, 'milestone_type', 'milestone', 
           """Ticket type for milestone-like tickets""")
 
    scheduler = ExtensionOption(cfgSection, 'scheduler', 
                                ITaskScheduler, 'SimpleScheduler')

    def __init__(self):
        self.env.log.debug('Initializing TracPM')

        # Configurable fields
        fields = ('percent', 'estimate', 'worked', 'start', 'finish',
                  'pred', 'succ', 'parent')

        self.fields = {}
        for field in fields:
            self.fields[field] = self.config.get(self.cfgSection,
                                                 'fields.%s' % field)
            # As of 0.11.6, there appears to be a bug in Option() so
            # that a defauilt of None isn't used and we get an empty
            # string instead.  We test for '' and make it None here.
            if self.fields[field] == '' or self.fields[field] == None:
                del(self.fields[field])
    
        # Tickets of this type will be displayed as milestones.
        self.milestoneType = self.config.get(self.cfgSection, 'milestone_type')

        # Hours per estimate unit.  
        #
        # If estimate is in hours, this is 1.
        #
        # If estimate is in days, this is may be 8 or 24, depending on
        # your needs and the setting of hoursPerDay
        self.hpe = float(self.config.get(self.cfgSection, 'hours_per_estimate'))

        # Default work in an unestimated task
        self.dftEst = float(self.config.get(self.cfgSection, 'default_estimate'))

        # How much to pad an estimate when a task has run over
        self.estPad = float(self.config.get(self.cfgSection, 'estimate_pad'))

	# Parent format option
	self.parent_format = self.config.get(self.cfgSection,'parent_format')

        # This is the format of start and finish in the Trac database
        self.dbDateFormat = str(self.config.get(self.cfgSection, 'date_format'))


    # Return True if all of the listed fields are configured, False
    # otherwise
    def isCfg(self, fields):
        if type(fields) == type([]):
            for f in fields:
                if f not in self.fields:
                    return False
        else:
            return fields in self.fields

        return True

    # Return True if ticket has a non-empty value for field, False
    # otherwise.
    def isSet(self, ticket, field):
        if self.isCfg(field) \
                and len(ticket[self.fields[field]]) != 0:
            return True
        else:
            return False
           
    # Parse the start field and return a datetime
    # Return None if the field is not configured or empty.
    def parseStart(self, ticket):
        if self.isSet(ticket, 'start'):
            return datetime(*time.strptime(ticket[self.fields['start']], 
                                       self.dbDateFormat)[0:7])
        else:
            return None

    # Parse the finish field and return a datetime
    # Return None if the field is not configured or empty.
    def parseFinish(self, ticket):
        if self.isSet(ticket, 'finish'):
            return datetime(*time.strptime(ticket[self.fields['finish']], 
                                           self.dbDateFormat)[0:7])
        else:
            return None

    # Return the integer ID of the parent ticket
    # 0 if no parent
    # None if parent is not configured
    def parent(self, ticket):
        if self.isCfg('parent'):
            return int(ticket[self.fields['parent']])
        else:
            return None

    # Return list of integer IDs of children.
    # None if parent is not configured.
    def children(self, ticket):
        return ticket['children']

    # Return a list of immediate precedessors for ticket or an empty
    # list if there are none.
    def predecessors(self, ticket):
        if self.isCfg('pred'):
            return ticket[self.fields['pred']]
        else:
            return []

    # Return a list of immediate successors for ticket or an empty
    # list if there are none.
    def successors(self, ticket):
        if self.isCfg('succ'):
            return ticket[self.fields['succ']]
        else:
            return []

    # Return computed start for ticket
    def start(self, ticket):
        return ticket['calc_start'][0]

    # Return computed start for ticket
    def finish(self, ticket):
        return ticket['calc_finish'][0]


    # Return a list of fields that PM needs to work.  The caller can
    # add this to the list of fields in a query so that when the
    # tickets are passed back to PM the necessary data is there.
    def queryFields(self):
        fields = []
        for field in self.fields:
            if self.isCfg(field):
                fields.append(self.fields[field])
        return fields

    # Return True if ticket is a milestone, False otherwise.
    def isMilestone(self, ticket):
        return ticket['type'] == self.milestoneType


    # Return hours of work in ticket as a floating point number
    def workHours(self, ticket):
        if self.isCfg('estimate') and ticket.get(self.fields['estimate']):
            est = float(ticket[self.fields['estimate']])
        else:
            est = None

        if self.isCfg('worked') and ticket.get(self.fields['worked']):
            work = float(ticket[self.fields['worked']])
        else:
            work = None

        # Milestones have no work.
        if ticket['type'] == self.milestoneType:
            est = 0.0
        # Closed tickets took as long as they took
        elif ticket['status'] == 'closed' and work:
            est = work
        # If the task is over its estimate, assume it will take
        # pad more time
        elif work > est:
            est = work + self.estPad
        # If unestimated, use the default
        elif not est or est == 0:
            est = self.dftEst
        # Otherwise, use the estimate parsed above.


        # Scale by hours per estimate
        hours = est * self.hpe

        return hours

    # Return percent complete as an integer
    # FIXME - or "worked/estimate"
    def percent(self, ticket):
        # Compute percent complete if given estimate and worked
        if self.isCfg(['estimate', 'worked']):
            # Try to compute the percent complete, default to 0
            try:
                worked = float(ticket[self.fields['worked']])
                if ticket['status'] == 'closed':
                    estimate = worked
                else:
                    estimate = self.workHours(ticket) / self.hpe
                percent = '%s/%s' % (worked, estimate)
            except:
                # Don't bother logging because 0 for an estimate is common.
                percent = 0
        # Closed tickets are 100% complete
        elif ticket['status'] == 'closed':
            percent = 100
        # Use percent if provided
        elif self.isCfg('percent'):
            try:
                percent = int(ticket[self.fields['percent']])
            except:
                percent = 0
        # If no estimate and worked (above) and no percent, it's 0
        else:
            percent = 0
            
        return percent


    # Returns pipe-delimited string of ticket IDs meeting PM
    # constraints.  Suitable for use as id field in ticket query
    # engine.
    # FIXME - dumb name
    def preQuery(self, options, this_ticket = None):
        # Expand the list of tickets in origins to include those
        # related through field.
        # origins is a list of strings
        def _expand(origins, field, format):
            if len(origins) == 0:
                return []

            node_list = [format % tid for tid in origins]
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            # FIXME - is this portable across DBMSs?
            cursor.execute("SELECT t.id "
                           "FROM ticket AS t "
                           "LEFT OUTER JOIN ticket_custom AS p ON "
                           "    (t.id=p.ticket AND p.name='%s') "
                           "WHERE p.value IN (%s)" % 
                           (field,
                            "'" + "','".join(node_list) + "'"))
            nodes = ['%s' % row[0] for row in cursor] 

            return origins + _expand(nodes, field, format)

        id = ''

        if options['root']:
            if options['root'] == 'self':
                if this_ticket:
                    nodes = [ this_ticket ]
                else:
                    nodes = []
            else:
                nodes = options['root'].split('|')

            id += '|'.join(_expand(nodes, 
                                    self.fields['parent'], 
                                    self.parent_format))

        if options['goal']:
            if options['goal'] == 'self':
                if this_ticket:
                    nodes = [ this_ticket ]
                else:
                    nodes = []
            else:
                nodes = options['goal'].split('|')

            id += '|'.join(_expand(nodes, 
                                    self.fields['succ'], 
                                    '%s'))

        return id

    # Add tasks for milestones related to the tickets
    def _add_milestones(self, options, tickets):
        if options.get('milestone'):
            milestones = options['milestone'].split('|')
        else:
            milestones = []

        # FIXME - Really?  This is a display option
        if not options['omitMilestones']:
            for t in tickets:
                if 'milestone' in t and \
                        t['milestone'] != '' and \
                        t['milestone'] not in milestones:
                    milestones.append(t['milestone'])

        # Need a unique ID for each task.
        if len(milestones) > 0:
            id = 0

            # Get the milestones and their due dates
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            # FIXME - is this portable across DBMSs?
            cursor.execute("SELECT name, due FROM milestone " +
                           "WHERE name in ('" + "','".join(milestones) + "')")
            for row in cursor:
                milestoneTicket = {}
                id = id-1
                milestoneTicket['id'] = id
                milestoneTicket['summary'] = row[0]
                milestoneTicket['description'] = 'Milestone %s' % row[0]
                milestoneTicket['milestone'] = row[0]
                # A milestone has no owner
                milestoneTicket['owner'] = ''
                milestoneTicket['type'] = self.milestoneType
                milestoneTicket['status'] = ''
                # Milestones are always shown
                milestoneTicket['level'] = 0
                
                # If there's no due date, default to today at close of business
                ts = row[1] or \
                    (datetime.now(utc) + 
                     timedelta(hours=options['hoursPerDay']))
                if self.isCfg('finish'):
                    milestoneTicket[self.fields['finish']] = \
                        format_date(ts, self.dbDateFormat)

                # jsGantt ignores start for a milestone but we use it
                # for scheduling.
                if self.isCfg(['start', 'finish']):
                    milestoneTicket[self.fields['start']] = \
                        milestoneTicket[self.fields['finish']]
                if self.isCfg('estimate'):
                    milestoneTicket[self.fields['estimate']] = 0
                # There is no percent complete for a milestone
                if self.isCfg('percent'):
                    milestoneTicket[self.fields['percent']] = 0
                # A milestone has no children or parent
                milestoneTicket['children'] = None
                if self.isCfg('parent'):
                    milestoneTicket[self.fields['parent']] = '0'
                # Place holder.
                milestoneTicket['link'] = ''
                # A milestone has no priority
                milestoneTicket['priority'] = 'n/a'

                # Any ticket with this as a milestone and no
                # successors has the milestone as a successor
                if self.isCfg(['pred', 'succ']):
                    pred = []
                    for t in tickets:
                        if not t['children'] and \
                                t['milestone'] == row[0] and \
                                t[self.fields['succ']] == []:
                            t[self.fields['succ']] = [ str(id) ]
                            pred.append(str(t['id']))
                    milestoneTicket[self.fields['pred']] = pred

                # A Trac milestone has no successors
                if self.isCfg('succ'):
                    milestoneTicket[self.fields['succ']] = []
                
                tickets.append(milestoneTicket)

    # Process the tickets to normalize formats, etc. to simplify
    # access functions.
    #
    # A 'children' field is added to each ticket.  If a 'parent' field
    # is configurd for PM, then 'children' is the (possibly empty)
    # list of children.  if there is no 'parent' field, then
    # 'children' is set to None.
    #
    # Milestones for the tickets are added pseudo-tickets.
    def postQuery(self, options, tickets):
        # ChildTicketsPlugin puts '#' at the start of the parent
        # field.  Strip it for simplicity.
        for t in tickets:
            if self.isCfg('parent'):
                parent = t[self.fields['parent']]
                if len(parent) > 0 and parent[0] == '#':
                    t[self.fields['parent']] = parent[1:]

        for t in tickets:
            # Clean up custom fields which might be null ('--') vs. blank ('')
            nullable = [ 'pred', 'succ', 
                         'start', 'finish', 
                         'parent', 
                         'worked', 'estimate', 'percent' ]
            for field in nullable:
                if self.isCfg(field):
                    if self.fields[field] not in t:
                        raise TracError('%s is not a custom ticket field' %
                                        self.fields[field])
                
                    if t[self.fields[field]] == '--':
                        t[self.fields[field]] = ''

            # Get list of children
            if self.isCfg('parent'):
                if t[self.fields['parent']] == '':
                    t[self.fields['parent']] = '0'
                
                t['children'] = [c['id'] for c in tickets \
                                     if c[self.fields['parent']] == \
                                     str(t['id'])]
            else:
                t['children'] = None

        for t in tickets:
            lists = [ 'pred', 'succ' ]
            for field in lists:
                if self.isCfg(field):
                    if t[self.fields[field]] == '':
                        t[self.fields[field]] = []
                    else:
                        t[self.fields[field]] = \
                            [s.strip() \
                                 for s in t[self.fields[field]].split(',')]

        self._add_milestones(options, tickets)

    def computeSchedule(self, options, tickets):
        self.scheduler.scheduleTasks(options, tickets)


# ========================================================================
# Handles dates, duration (estimate) and dependencies but not resource
# leveling.  
#
# Assumes a 5-day work week (Monday-Friday) and options['hoursPerDay']
# for every resource.
#
# A Note About Working Hours
#
# The naive scheduling algorithm in the plugin assumes all resources
# work the same number of hours per day.  That limit can be configured
# (hoursPerDay) but defaults to 8.0.  While is is likely that these
# hours are something like 8am to 4pm (or 8am to 5pm, minus an hour
# lunch), daily scheduling isn't concerned with which hours are
# worked, only how many are worked each day.  To simplify range
# checking throughout the scheduler, calculations are done as if the
# work day starts at midnight (hour==0) and continues for the
# configured number of hours per day (e.g., 00:00..08:00).
class SimpleScheduler(Component):
    implements(ITaskScheduler)

    pm = None

    def __init__(self):
        # Instantiate the PM component
        self.pm = TracPM(self.env)


    # ITaskScheduler method
    # Uses options hoursPerDay and schedule (alap or asap).
    def scheduleTasks(self, options, tickets):
        # Faster lookups
        self.ticketsByID = {}
        for t in tickets:
            self.ticketsByID[t['id']] = t

        # Return a time delta hours (positive or negative) from
        # fromDate, accounting for working hours and weekends.
        #
        # FIXME - this needs a ticket or a resource so it can call use
        # IResourceCalendar.
        def _calendarOffset(hours, fromDate):
            if hours < 0:
                sign = -1
            else:
                sign = 1

            # Normalize hours into days and weeks.
            # Note: hours, days, and weeks all have the same sign
            # Figure out days from hours
            days = int(hours / options['hoursPerDay'])
            hours -= (days * options['hoursPerDay'])
            # Figure out weeks from days
            weeks = int(days / 7.0)
            days -= (weeks * 7)
            
            # If we're at the start of the work day and moving
            # forwards or the end of the work day and moving
            # backwards, one day of hours are worked today so move
            # hours from days to hours
            endOfDay = fromDate.replace(hour=0, minute=0)
            if fromDate == endOfDay or \
                    fromDate == endOfDay + \
                    timedelta(hours=options['hoursPerDay']):
                days -= 1 * sign
                hours += options['hoursPerDay'] * sign
                
            # If the new time is outside business hours, skip
            # non-business hours
            toDate = fromDate + timedelta(weeks=weeks, days=days, hours=hours)
            endOfDay = toDate.replace(hour=0, minute=0) + \
                timedelta(hours=options['hoursPerDay'])
            if toDate > endOfDay:
                hours += (24-options['hoursPerDay']) * sign

            # If the new time is on the weekend, skip the weekend
            toDate = fromDate + timedelta(weeks=weeks, days=days, hours=hours)
            if toDate.weekday() > 4:
                days += 2 * sign
                
            return timedelta(weeks=weeks, days=days, hours=hours)            


        # Return True if d1 is better than d2
        # Each is a tuple in the form [date, explicit] or None
        def _betterDate(d1, d2):
            # If both are None, neither is better
            if d1 == None and d2 == None:
                better = False
            # If d1 is None, d2 is better if it is explicit
            # That is, don't replace "not yet set" with an implicit date
            elif d1 == None:
                better = d2[1]
            # If d2 is None, d1 has to be better
            elif d2 == None:
                better = True
            # If d1 is explicit
            elif d1[1]:
                # If d2 is implicit, d1 is better
                if not d2[1]:
                    better = True
                # If d2 is also explicit, d1 isn't better
                else:
                    better = False
            # d1 is implicit, it can't be better than d2
            else:
                better = False

            if (better):
                self.env.log.debug('%s is better than %s' % (d1, d2))
            else:
                self.env.log.debug('%s is NOT better than %s' % (d1, d2))
                
            return better
                
        # TODO: If we have start and estimate, we can figure out
        # finish (opposite case of figuring out start from finish and
        # estimate as we do now).  

        # Schedule a task As Late As Possible
        #
        # Return a tuple like [start, explicit] where 
        #   start is the start of the task as a date object
        #
        #   explicit is True if start was parsed from a user
        #   specified value and False if it was it is inferred as
        #   today
        def _schedule_task_alap(t):
            # Find the finish of the closest ancestor with one set (if any)
            def _ancestor_finish(t):
                finish = None
                # If there are parent and finish fields
                if self.pm.isCfg(['finish', 'parent']):
                    pid = self.pm.parent(t)
                    # If this ticket has a parent, process it
                    if pid != 0:
                        if pid in self.ticketsByID:
                            parent = self.ticketsByID[pid]
                            _schedule_task_alap(parent)
                            if _betterDate(self.ticketsByID[pid]['calc_finish'], 
                                           finish):
                                finish = self.ticketsByID[pid]['calc_finish']
                        else:
                            self.env.log.info(('Ticket %s has parent %s ' +
                                               'but %s is not in the chart.' +
                                               'Ancestor deadlines ignored.') %
                                              (t['id'], pid, pid))

                return finish

            # Find the earliest start of any successor
            # t is a ticket (list of ticket fields)
            # start is a tuple ([date, explicit])
            def _earliest_successor(t, start):
                for id in self.pm.successors(t):
                    id = int(id)
                    if id in self.ticketsByID:
                        s = _schedule_task_alap(self.ticketsByID[id])
                        if _betterDate(s, start) and \
                                start == None or \
                                (s and start and s[0] < start[0]):
                            start = s
                    else:
                        self.env.log.info(('Ticket %s has successor %s ' +
                                           'but %s is not in the chart. ' +
                                           'Dependency deadlines ignored.') %
                                          (t['id'], id, id))
                return start

            # If we haven't scheduled this yet, do it now.
            if t.get('calc_finish') == None:
                # If there is a finish set, use it
                if self.pm.isSet(t, 'finish'):
                    finish = self.pm.parseFinish(t)
                    finish = finish.replace(hour=0, minute=0) + \
                        timedelta(hours=options['hoursPerDay'])
                    finish = [finish, True]
                # Otherwise, compute finish from dependencies.
                else:
                    finish = _earliest_successor(t, _ancestor_finish(t))
                    
                    # If dependencies don't give a date, default to
                    # today at close of business
                    if finish == None:
                        finish = datetime.today().replace(hour=0, 
                                                          minute=0) + \
                            timedelta(hours=options['hoursPerDay'])
                        # If today is on a weekend, move back to Friday
                        if finish.weekday() > 4:
                            finish += timedelta(days=7-finish.weekday())
                        finish = [finish, False]
                    # If we are to finish at the beginning of the work
                    # day, our finish is really the end of the previous
                    # work day
                    elif finish[0] == finish[0].replace(hour=0, minute=0):
                        # Tuesday-Friday, back up to end of previous day
                        f = finish[0]
                        if f.weekday() > 0:
                            f -= timedelta(hours=24-options['hoursPerDay'])
                        # Monday, skip the weekend, too.
                        else:
                            f -= timedelta(hours=(24-options['hoursPerDay'])+48)
                        finish = [f, finish[1]]

                # Set the field
                t['calc_finish'] = finish

            if t.get('calc_start') == None:
                if self.pm.isSet(t, 'start'):
                    start = self.pm.parseStart(t)
                    start = start.replace(hour=0, minute=0) + \
                        timedelta(hours=options['hoursPerDay'])
                    start = [start, True]
                else:
                    hours = self.pm.workHours(t)
                    start = t['calc_finish'][0] + \
                        _calendarOffset(-1*hours, t['calc_finish'][0])
                    start = [start, t['calc_finish'][1]]

                t['calc_start'] = start

            return t['calc_start']

        # Schedule a task As Soon As Possible
        # Return the finish of the task as a date object
        def _schedule_task_asap(t):
            # Find the start of the closest ancestor with one set (if any)
            def _ancestor_start(t):
                start = None
                # If there are parent and start fields
                if self.pm.isCfg(['start', 'parent']):
                    pid = self.pm.parent(t)
                    # If this ticket has a parent, process it
                    if pid != 0:
                        if pid in self.ticketsByID:
                            parent = self.ticketsByID[pid]
                            _schedule_task_asap(parent)
                            if _betterDate(self.ticketsByID[pid]['calc_start'], 
                                           start):
                                start = self.ticketsByID[pid]['calc_start']
                        else:
                            self.env.log.info(('Ticket %s has parent %s ' +
                                               'but %s is not in the chart. ' +
                                               'Ancestor deadlines ignored.') %
                                              (t['id'], pid, pid))

                return start

            # Find the latest finish of any predecessor
            # t is a ticket (list of ticket fields)
            # start is a tuple ([date, explicit])
            def _latest_predecessor(t, finish):
                for id in self.pm.predecessors(t):
                    id = int(id)
                    if id in self.ticketsByID:
                        f = _schedule_task_asap(self.ticketsByID[id])
                        if _betterDate(f, finish) and \
                                finish == None or \
                                (f and finish and f[0] > finish[0]):
                            finish = f
                    else:
                        self.env.log.info(('Ticket %s has predecessor %s ' +
                                           'but %s is not in the chart. ' +
                                           'Dependency deadlines ignored.') %
                                          (t['id'], id, id))
                return finish

            # If we haven't scheduled this yet, do it now.
            if t.get('calc_start') == None:
                # If there is a start set, use it
                if self.pm.isSet(t, 'start'):
                    start = self.pm.parseStart(t)
                    start = start.replace(hour=0, minute=0)
                    start = [start, True]
                # Otherwise, compute start from dependencies.
                else:
                    start = _latest_predecessor(t, _ancestor_start(t))
                    
                    # If dependencies don't give a date, default to today
                    if start == None:
                        start = datetime.today().replace(hour=0, minute=0)

                        # FIXME - do the converse in ALAP, too.
                        # If today is on a weekend, move ahead to Monday
                        if start.weekday() > 4:
                            start += timedelta(days=7-start.weekday())
                        start = [start, False]
                    # If we are to start at the end of the work
                    # day, our start is really the beginning of the next
                    # work day
                    elif start[0] == start[0].replace(hour=0, minute=0) + \
                            timedelta(hours=options['hoursPerDay']):
                        # Monday-Thursday, move ahead to beginning of
                        # previous day
                        s = start[0]
                        if s.weekday() < 4:
                            s += timedelta(hours=24-options['hoursPerDay'])
                        # Friday, skip the weekend, too.
                        else:
                            s += timedelta(hours=(24-options['hoursPerDay'])+48)
                        start = [s, start[1]]
                
                # Set the field
                t['calc_start'] = start
                
            if t.get('calc_finish') == None:
                if self.pm.isSet(t, 'finish'):
                    finish = self.pm.parseFinish(t)
                    finish = finish.replace(hour=0, minute=0)
                    finish = [finish, True]
                else:
                    hours = self.pm.workHours(t)
                    finish = t['calc_start'][0] + \
                        _calendarOffset(+1*hours, t['calc_start'][0])
                    finish = [finish, start[1]]
                t['calc_finish'] = finish

            return t['calc_finish']


        for id in self.ticketsByID:
            if options['schedule'] == 'alap':
                _schedule_task_alap(self.ticketsByID[id])
            else:
                _schedule_task_asap(self.ticketsByID[id])

# ========================================================================
class TracJSGanttSupport(Component):
    implements(IRequestFilter, ITemplateProvider)
    
    Option('trac-jsgantt', 'hours_per_estimate', '1', 
           """Hours represented by each unit of estimated work""")
    Option('trac-jsgantt', 'default_estimate', '4.0', 
           """Default work for an unestimated task, same units as estimate""")
    Option('trac-jsgantt', 'estimate_pad', '0.0', 
           """How much work may be remaining when a task goes over estimate, same units as estimate""")
    Option('trac-jsgantt', 'date_format', '%Y-%m-%d', 
           """Format for ''start'' and ''finish'' date strings""")    
    
    Option('trac-jsgantt', 'option.format', 'day', 
           """Initial format of Gantt chart""")
    Option('trac-jsgantt', 'option.formats', 'day|week|month|quarter', 
           """Formats to show for Gantt chart""")
    IntOption('trac-jsgantt', 'option.sample', 0,
              """Show sample Gantt""")
    IntOption('trac-jsgantt', 'option.res', 1, 
              """Show resource column""")
    IntOption('trac-jsgantt', 'option.dur', 1, 
              """Show duration column""")              
    IntOption('trac-jsgantt', 'option.comp', 1,
              """Show percent complete column""")              
    Option('trac-jsgantt', 'option.caption', 'Resource',
           """Caption to follow task in Gantt""")
    IntOption('trac-jsgantt', 'option.startDate', 1, 
              """Show start date column""")
    IntOption('trac-jsgantt', 'option.endDate', 1, 
              """Show finish date column""")
    Option('trac-jsgantt', 'option.dateDisplay', 'mm/dd/yyyy', 
           """Format to display dates""")
    IntOption('trac-jsgantt', 'option.openLevel', 999, 
              """How many levels of task hierarchy to show open""")
    IntOption('trac-jsgantt', 'option.expandClosedTickets', 1, 
              """Show children of closed tasks in the task hierarchy""")
    Option('trac-jsgantt', 'option.colorBy', 'priority', 
           """Field to use to color tasks""")
    IntOption('trac-jsgantt', 'option.lwidth', None, 
              """Width (in pixels) of left table""")
    IntOption('trac-jsgantt', 'option.root', None,
              """Ticket(s) to show descendants of""")
    IntOption('trac-jsgantt', 'option.goal', None,
              """Ticket(s) to show predecessors of""")
    IntOption('trac-jsgantt', 'option.showdep', 1, 
              """Show dependencies in Gantt""")
    IntOption('trac-jsgantt', 'option.userMap', 1, 
              """Map user IDs to user names""")
    IntOption('trac-jsgantt', 'option.omitMilestones', 0,
              """Omit milestones""")
    Option('trac-jsgantt', 'option.schedule', 'alap',
           """Schedule algorithm: alap or asap""")
    # This seems to be the first floating point option.
    Option('trac-jsgantt', 'option.hoursPerDay', '8.0',
                """Hours worked per day""")
     

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('tracjsgantt', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        # I think we should look for a TracJSGantt on the page and set
        # a flag for the post_process_request handler if found
        return handler
            
    def post_process_request(self, req, template, data, content_type):
        add_script(req, 'tracjsgantt/jsgantt.js')
        add_stylesheet(req, 'tracjsgantt/jsgantt.css')
        add_stylesheet(req, 'tracjsgantt/tracjsgantt.css')
        return template, data, content_type


class TracJSGanttChart(WikiMacroBase):
    """
Displays a Gantt chart for the specified tickets.

The chart display can be controlled with a number of macro arguments:

||'''Argument'''||'''Description'''||'''Default'''||
|| `formats`||What to display in the format control.  A pipe-separated list of `minute`, `hour`, `day`, `week`, `month`, and `quarter` (though `minute` may not be very useful). ||'day|week|month|quarter'||
|| `format`||Initial display format, one of those listed in `formats` || First format ||
|| `sample`||Display sample tasks (1) or not (0) || 0 ||
|| `res`||Show resource column (1) or not (0) || 1 ||
|| `dur`||Show duration colunn (1) or not (0) || 1 ||
|| `comp`||Show percent complete column (1) or not (0) || 1 ||
|| `caption`||Caption to place to right of tasks: None, Caption, Resource, Duration, %Complete || Resource ||
|| `startDate`||Show start date column (1) or not (0) || 1 ||
|| `endDate`||Show end date column (1) or not (0) || 1 ||
|| `dateDisplay`||Date display format: 'mm/dd/yyyy', 'dd/mm/yyyy', or 'yyyy-mm-dd' || 'mm/dd/yyyy' ||
|| `openLevel`||Number of levels of tasks to show.  1 = only top level task.  || 999 ||
|| `colorBy`||Field to use to choose task colors.  Each unique value of the field will have a different color task.  Other likely useful values are owner and milestone but any field can be used. || priority ||
|| `root`||When using something like Subtickets plugin to maintain a tree of tickets and subtickets, you may create a Gantt showing a ticket and all of its descendants with `root=<ticket#>`.  The macro uses the configured `parent` field to find all descendant tasks and build an `id=` argument for Trac's native query handler.[[br]][[br]]Multiple roots may be provided like `root=1|12|32`.[[br]][[br]]When used in a ticket description or comment, `root=self` will display the current ticket's descendants.||None||
|| `goal`||When using something like MasterTickets plugin to maintain ticket dependencies, you may create a Gantt showing a ticket and all of its predecessors with `goal=<ticket#>`.  The macro uses the configured `succ` field to find all predecessor tasks and build an `id=` argument for Trac's native query handler.[[br]][[br]]Multiple goals may be provided like `goal=1|12|32`.[[br]][[br]]When used in a ticket description or comment, `goal=self` will display the current ticket's predecessors.||None||
|| `lwidth`||The width, in pixels, of the table of task names, etc. on the left of the Gantt. || ||
|| `showdep`||Show dependencies (1) or not (0)||1||
|| `userMap`||Map user !IDs to full names (1) or not (0).||1||
|| `omitMilestones`||Show milestones for displayed tickets (0) or only those specified by `milestone=` (1)||0||
|| `schedule`||Schedule tasks based on dependenies and estimates.  Either as soon as possible (asap) or as late as possible (alap)||alap||

Site-wide defaults for macro arguments may be set in `trac.ini`.  `option.<opt>` overrides the built-in default for `<opt>` from the table above.

All other macro arguments are treated as TracQuery specification (e.g., milestone=ms1|ms2) to control which tickets are displayed.

    """

    pm = None

    def __init__(self):
        # Instantiate the PM component
        self.pm = TracPM(self.env)

        self.GanttID = 'g'


        # All the macro's options with default values.
        # Anything else passed to the macro is a TracQuery field.
        options = ('format', 'formats', 'sample', 'res', 'dur', 'comp', 
                   'caption', 'startDate', 'endDate', 'dateDisplay', 
                   'openLevel', 'expandClosedTickets', 'colorBy', 'lwidth', 
                   'root', 'goal', 'showdep', 'userMap', 'omitMilestones',
                   'schedule', 'hoursPerDay')

        self.options = {}
        for opt in options:
            self.options[opt] = self.config.get('trac-jsgantt',
                                                'option.%s' % opt)


        # These have to be in sync.  jsDateFormat is the date format
        # that the JavaScript expects dates in.  It can be one of
        # 'mm/dd/yyyy', 'dd/mm/yyyy', or 'yyyy-mm-dd'.  pyDateFormat
        # is a strptime() format that matches jsDateFormat.  As long
        # as they are in sync, there's no real reason to change them.
        self.jsDateFormat = 'yyyy-mm-dd'
        self.pyDateFormat = '%Y-%m-%d %H:%M'

        # Hours per estimate unit.  
        #
        # If estimate is in hours, this is 1.
        #
        # If estimate is in days, this is may be 8 or 24, depending on
        # your needs and the setting of hoursPerDay
        self.hpe = float(self.config.get('trac-jsgantt', 'hours_per_estimate'))

        # Default work in an unestimated task
        self.dftEst = float(self.config.get('trac-jsgantt', 
                                            'default_estimate'))

        # How much to pad an estimate when a task has run over
        self.estPad = float(self.config.get('trac-jsgantt', 
                                            'estimate_pad'))

        # User map (login -> realname) is loaded on demand, once.
        # Initialization to None means it is not yet initialized.
        self.user_map = None


    def _begin_gantt(self, options):
        if options['format']:
            defaultFormat = options['format']
        else:
            defaultFormat = options['formats'].split('|')[0]
        showdep = options['showdep']
        text = ''
        text += '<div style="position:relative" class="gantt" id="GanttChartDIV_'+self.GanttID+'"></div>\n'
        text += '<script language="javascript">\n'
        text += 'var '+self.GanttID+' = new JSGantt.GanttChart("'+ \
            self.GanttID+'",document.getElementById("GanttChartDIV_'+ \
            self.GanttID+'"), "%s", "%s");\n' % \
            (javascript_quote(defaultFormat), showdep)
        text += 'var t;\n'
        text += 'if (window.addEventListener){\n'
        text += '  window.addEventListener("resize", function() { g.Draw();\n }, false);\n'
        text += '} else {\n'
        text += '  window.attachEvent("onresize", function() { g.Draw();\n });\n'
        text += '}\n'
        return text

    def _end_gantt(self, options):
        chart = ''
        chart += self.GanttID+'.Draw();\n' 
        if options['showdep']:
            chart += self.GanttID+'.DrawDependencies();\n'
        chart += '</script>\n'
        return chart

    def _gantt_options(self, options):
        opt = ''
        opt += self.GanttID+'.setShowRes(%s);\n' % options['res']
        opt += self.GanttID+'.setShowDur(%s);\n' % options['dur']
        opt += self.GanttID+'.setShowComp(%s);\n' % options['comp']
        w = options['lwidth']
        if w:
            opt += self.GanttID+'.setLeftWidth(%s);\n' % w
            

        opt += self.GanttID+'.setCaptionType("%s");\n' % \
            javascript_quote(options['caption'])

        opt += self.GanttID+'.setShowStartDate(%s);\n' % options['startDate']
        opt += self.GanttID+'.setShowEndDate(%s);\n' % options['endDate']

        opt += self.GanttID+'.setDateInputFormat("%s");\n' % \
            javascript_quote(self.jsDateFormat)

        opt += self.GanttID+'.setDateDisplayFormat("%s");\n' % \
            javascript_quote(options['dateDisplay'])

        opt += self.GanttID+'.setFormatArr(%s);\n' % ','.join(
            '"%s"' % javascript_quote(f) for f in options['formats'].split('|'))
        opt += self.GanttID+'.setPopupFeatures("location=1,scrollbars=1");\n'
        return opt

    # TODO - use ticket-classN styles instead of colors?
    def _add_sample_tasks(self):
        tasks = ''
        tasks = self.GanttID+'.setDateInputFormat("mm/dd/yyyy");'

        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(1,   "Define Chart API",     "",          "",          "#ff0000", "http://help.com", 0, "Brian",     0, 1, 0, 1, '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(11,  "Chart Object",         "2/20/2011", "2/20/2011", "#ff00ff", "http://www.yahoo.com", 1, "Shlomy",  100, 0, 1, 1, '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(12,  "Task Objects",         "",          "",          "#00ff00", "", 0, "Shlomy",   40, 1, 1, 1, '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(121, "Constructor Proc",     "2/21/2011", "3/9/2011",  "#00ffff", "http://www.yahoo.com", 0, "Brian T.", 60, 0, 12, 1, '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(122, "Task Variables",       "3/6/2011",  "3/11/2011", "#ff0000", "http://help.com", 0, "",         60, 0, 12, 1,121, '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(123, "Task Functions",       "3/9/2011",  "3/29/2011", "#ff0000", "http://help.com", 0, "Anyone",   60, 0, 12, 1, 0, "This is another caption", '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(2,   "Create HTML Shell",    "3/24/2011", "3/25/2011", "#ffff00", "http://help.com", 0, "Brian",    20, 0, 0, 1,122, '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(3,   "Code Javascript",      "",          "",          "#ff0000", "http://help.com", 0, "Brian",     0, 1, 0, 1 , '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(31,  "Define Variables",     "2/25/2011", "3/17/2011", "#ff00ff", "http://help.com", 0, "Brian",    30, 0, 3, 1, 0,"Caption 1", '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(32,  "Calculate Chart Size", "3/15/2011", "3/24/2011", "#00ff00", "http://help.com", 0, "Shlomy",   40, 0, 3, 1, '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(33,  "Draw Taks Items",      "",          "",          "#00ff00", "http://help.com", 0, "Someone",  40, 1, 3, 1, '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(332, "Task Label Table",     "3/6/2011",  "3/11/2011", "#0000ff", "http://help.com", 0, "Brian",    60, 0, 33, 1, '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(333, "Task Scrolling Grid",  "3/9/2011",  "3/20/2011", "#0000ff", "http://help.com", 0, "Brian",    60, 0, 33, 1, '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(34,  "Draw Task Bars",       "",          "",          "#990000", "http://help.com", 0, "Anybody",  60, 1, 3, 1, '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(341, "Loop each Task",       "3/26/2011", "4/11/2011", "#ff0000", "http://help.com", 0, "Brian",    60, 0, 34, 1, "332,333", '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(342, "Calculate Start/Stop", "4/12/2011", "5/18/2011", "#ff6666", "http://help.com", 0, "Brian",    60, 0, 34, 1, '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(343, "Draw Task Div",        "5/13/2011", "5/17/2011", "#ff0000", "http://help.com", 0, "Brian",    60, 0, 34, 1, '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(344, "Draw Completion Div",  "5/17/2011", "6/04/2011", "#ff0000", "http://help.com", 0, "Brian",    60, 0, 34, 1, '+self.GanttID+'));\n'
        tasks += self.GanttID+'.AddTaskItem(new JSGantt.TaskItem(35,  "Make Updates",         "10/17/2011","12/04/2011","#f600f6", "http://help.com", 0, "Brian",    30, 0, 3,  1, '+self.GanttID+'));\n'
        return tasks

    # Get the required columns for the tickets which match the
    # criteria in options.
    def _query_tickets(self, options):
        query_args = {}
        for key in options.keys():
            if not key in self.options:
                query_args[key] = options[key]

        # Expand (or set) list of IDs to include those specified by PM
        # query meta-options (e.g., root)
        pm_id = self.pm.preQuery(options, self._this_ticket())
        if pm_id != '':
            if 'id' in query_args:
                query_args['id'] += '|' + pm_id
            else:
                query_args['id'] = pm_id

        # Start with values that are always needed
        fields = [
            'description', 
            'owner', 
            'type', 
            'status', 
            'summary', 
            'milestone', 
            'priorty'] 

        # Add configured fields
        fields += self.pm.queryFields()

        # Make sure the coloring field is included
        if 'colorBy' in options and options['colorBy'] not in fields:
            fields.append(options['colorBy'])

        # Make the query argument
        query_args['col'] = "|".join(fields)  

        # Construct the querystring. 
        query_string = '&'.join(['%s=%s' % 
                                 (f, str(v)) for (f, v) in 
                                 query_args.iteritems()]) 

        # Get the Query Object. 
        query = Query.from_string(self.env, query_string)

        # Get all tickets 
 	rawtickets = query.execute(self.req) 

 	# Do permissions check on tickets 
 	tickets = [t for t in rawtickets  
                   if 'TICKET_VIEW' in self.req.perm('ticket', t['id'])] 

        return tickets

    def _compare_tickets(self, t1, t2):
        # If t2 depends on t1, t2 is first
        if str(t1['id']) in self.pm.successors(t2):
            return 1
        # If t1 depends on t2, t1 is first
        elif str(t2['id']) in self.pm.successors(t1):
            return -1
        # If t1 ends first, it's first
        elif self.pm.finish(t1) < self.pm.finish(t2):
            return -1
        # If t2 ends first, it's first
        elif self.pm.finish(t1) > self.pm.finish(t2):
            return 1
        # End dates are same. If t1 starts later, it's later
        elif self.pm.start(t1) > self.pm.start(t2):
            return 1
        # Otherwise, preserve order (assume t1 is before t2 when called)
        else:
            return 0

    # Compute WBS for sorting and figure out the tickets' levels for
    # controlling how many levels are open.  
    #
    # WBS is a list like [ 2, 4, 1] (the first child of the fourth
    # child of the second top-level element).
    def _compute_wbs(self):
        # Set the ticket's level and wbs then recurse to children.
        def _setLevel(id, wbs, level):
            # Update this node
            self.ticketsByID[id]['level'] = level
            self.ticketsByID[id]['wbs'] = copy.copy(wbs)

            # Recurse to children
            childIDs = self.pm.children(self.ticketsByID[id])
            if childIDs:
                childTickets = [self.ticketsByID[id] for id in childIDs]
                childTickets.sort(self._compare_tickets)
                childIDs = [ct['id'] for ct in childTickets]
                
                # Add another level
                wbs.append(1)
                for c in childIDs:
                    wbs = _setLevel(c, wbs, level+1)
                # Remove the level we added
                wbs.pop()
            

            # Increment last element of wbs
            wbs[len(wbs)-1] += 1

            return wbs

        # Set WBS and level on all top level tickets (and recurse) If
        # a ticket's parent is not in the viewed tickets, consider it
        # top-level
        wbs = [ 1 ]
        for t in self.tickets:
            if self.pm.parent(t) == None \
                    or self.pm.parent(t) == 0 \
                    or self.pm.parent(t) not in self.ticketsByID.keys():
                wbs = _setLevel(t['id'], wbs, 1)


    def _task_display(self, t, options):
        def _buildMap(field):
            self.classMap = {}
            i = 0
            for t in self.tickets:
                if t[field] not in self.classMap:
                    i = i + 1
                    self.classMap[t[field]] = i

        def _buildEnumMap(field):
            self.classMap = {}
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT name," + 
                           db.cast('value', 'int') + 
                           " FROM enum WHERE type=%s", (field,))
            for name, value in cursor:
                self.classMap[name] = value

        display = None
        colorBy = options['colorBy']

        # Build the map the first time we need it
        if self.classMap == None:
            # Enums (TODO: what others should I list?)
            if options['colorBy'] in ['priority', 'severity']:
                _buildEnumMap(colorBy)
            else:
                _buildMap(colorBy)

        # Set display based on class map
        if t[colorBy] in self.classMap:
            display = 'class=ticket-class%d' % self.classMap[t[colorBy]]

        # Add closed status for strike through
        if t['status'] == 'closed':
            if display == None:
                display = 'class=ticket-closed'
            else:
                display += ' ticket-closed'

        if display == None:
            display = '#ff7f3f'
        return display
        

    # Format a ticket into JavaScript source to display the task. t is
    # expected to have:
    #   children - child ticket IDs or None
    #   description - ticket description.
    #   id - ticket ID, an integer
    #   level - levels from root (0)
    #   link - What to link to
    #   owner - Used as resource name.
    #   percent - integer percent complete, 0..100 (or "act/est")
    #   priority - used to color the task
    #   self.fields[finish] - end date (ignored if children is not None)
    #   self.fields[parent] - parent ticket ID
    #   self.fields[pred] - predecessor ticket IDs
    #   self.fields[start] - start date (ignored if children is not None)
    #   status - string displayed in tool tip ; FIXME - not displayed yet
    #   summary - ticket summary
    #   type - string displayed in tool tip FIXME - not displayed yet
    def _format_ticket(self, ticket, options):
        # Translate owner to full name
        def _owner(ticket):
            if self.pm.isMilestone(ticket):
                owner_name = ''
            else:
                owner_name = ticket['owner']
                if options['userMap']:
                    # Build the map the first time we use it
                    if self.user_map is None:
                        self.user_map = {}
                        for username, name, email in self.env.get_known_users():
                            self.user_map[username] = name
                    # Map the user name
                    if self.user_map.get(owner_name):
                        owner_name = self.user_map[owner_name]
            return owner_name
            
        task = ''

        # pID, pName
        if self.pm.isMilestone(ticket):
            if ticket['id'] > 0:
                # Put ID number on inchpebbles
                name = 'MS:%s (#%s)' % (ticket['summary'], ticket['id'])
            else:
                # Don't show bogus ID of milestone pseudo tickets.
                name = 'MS:%s' % ticket['summary']
        else:
            name = "#%d:%s (%s %s)" % \
                   (ticket['id'], ticket['summary'],
                    ticket['status'], ticket['type'])
        task += 't = new JSGantt.TaskItem(%d,"%s",' % \
            (ticket['id'], javascript_quote(name))

        # pStart, pEnd
        task += '"%s",' % self.pm.start(ticket).strftime(self.pyDateFormat)
        task += '"%s",' % self.pm.finish(ticket).strftime(self.pyDateFormat)

        # pDisplay
        task += '"%s",' % javascript_quote(self._task_display(ticket, options))

        # pLink
        task += '"%s",' % javascript_quote(ticket['link'])

        # pMile
        if self.pm.isMilestone(ticket):
            task += '1,'
        else:
            task += '0,'

        # pRes (owner)
        task += '"%s",' % javascript_quote(_owner(ticket))

        # pComp (percent complete); integer 0..100
        task += '"%s",' % self.pm.percent(ticket)

        # pGroup (has children)
        if self.pm.children(ticket):
            task += '%s,' % 1
        else:
            task += '%s,' % 0
        
        # pParent (parent task ID) 
        # If there's no parent field configured, don't link to parents
        if self.pm.parent(ticket) == None:
            task += '%s,' % 0
        # If there's a parent field, but the ticket is in root, don't
        # link to parent
        elif options['root'] and str(ticket['id']) in options['root'].split('|'):
            task += '%s,' % 0
        # If there's a parent field, root == self and this ticket is self, 
        # don't link to parents
        elif options['root'] and \
                options['root'] == 'self' and \
                str(ticket['id']) == self._this_ticket():
            task += '%s,' % 0
        # If there's a parent, and the ticket is not a root, link to parent
        else:
            task += '%s,' % self.pm.parent(ticket)

        # open
        if ticket['level'] < options['openLevel'] and \
                ((options['expandClosedTickets'] != 0) or \
                     (ticket['status'] != 'closed')):
            open = 1
        else:
            open = 0
        task += '%d,' % open

        # predecessors
        pred = self.pm.predecessors(ticket)
        if len(pred):
            task += '"%s",' % javascript_quote(','.join(pred))
        else:
            task += '"%s",' % javascript_quote(','.join(''))
        
        # caption 
        # FIXME - if caption isn't set to caption, use "" because the
        # description could be quite long and take a long time to make
        # safe and display.
        task += '"%s (%s %s)"' % (javascript_quote(ticket['description']),
                                  javascript_quote(ticket['status']),
                                  javascript_quote(ticket['type']))
        task += ', ' + self.GanttID
        task += ');\n'
        task += self.GanttID+'.AddTaskItem(t);\n'
        return task

    def _add_tasks(self, options):
        if options.get('sample'):
            tasks = self._add_sample_tasks()
        else:
            tasks = ''
            self.tickets = self._query_tickets(options)

            # Post process the query to add and compute fields so
            # displaying the tickets is easy
            self.pm.postQuery(options, self.tickets)

            # Faster lookups for WBS and scheduling.
            self.ticketsByID = {}
            for t in self.tickets:
                self.ticketsByID[t['id']] = t

            # Schedule the tasks
            self.pm.computeSchedule(options, self.tickets)

            # Sort tickets by date for computing WBS
            self.tickets.sort(self._compare_tickets)

            # Compute the WBS and sort them by WBS for display
            self._compute_wbs()                
            self.tickets.sort(key=itemgetter('wbs'))

            # Set the link for clicking through the Gantt chart
            for t in self.tickets:
                if t['id'] > 0:
                    t['link'] = self.req.href.ticket(t['id'])
                else:
                    t['link'] = self.req.href.milestone(t['summary'])


            for ticket in self.tickets:
                tasks += self._format_ticket(ticket, options)

        return tasks

    def _parse_options(self, content):
        _, options = parse_args(content, strict=False)

        for opt in self.options.keys():
            if opt in options:
                # FIXME - test for success, log on failure
                if isinstance(self.options[opt], (int, long)):
                    options[opt] = int(options[opt])
            else:
                options[opt] = self.options[opt]

        # FIXME - test for success, log on failure
        options['hoursPerDay'] = float(options['hoursPerDay'])

        return options
 
    def _this_ticket(self):
        matches = re.match('/ticket/(\d+)', self.req.path_info)
        if not matches:
            return None
        return matches.group(1)

    def expand_macro(self, formatter, name, content):
        self.req = formatter.req

        # Each invocation needs to build its own map.
        self.classMap = None

        options = self._parse_options(content)

        self.GanttID = 'g_'+ str(time.time()).replace('.','')
        chart = ''
        tasks = self._add_tasks(options)
        if len(tasks) == 0:
            chart += 'No tasks selected.'
        else:
            chart += self._begin_gantt(options)
            chart += self._gantt_options(options)
            chart += tasks
            chart += self._end_gantt(options)

        return chart
