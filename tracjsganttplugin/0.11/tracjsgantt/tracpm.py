import re
import time
import math
import copy
from datetime import timedelta, datetime


from trac.util.datefmt import format_date, utc
from trac.ticket.query import Query

from trac.config import IntOption, Option, ExtensionOption
from trac.core import implements, Component, TracError, Interface

class IResourceCalendar(Interface):
    # Return the number of hours available for the resource on the
    # specified date.
    # FIXME - should this be pm_hoursAvailable or something so other
    # plugins can implement it without potential conflict?
    def hoursAvailable(self, date, resource = None):
        """Called to see how many hours are available on date"""

class ITaskScheduler(Interface):
    # Schedule each the ticket in tickets with consideration for
    # dependencies, estimated work, hours per day, etc.
    # 
    # ticketsByID is a dictionary, indexed by numeric ticket ID, each
    # ticket contains at least the fields returned by queryFields()
    # and the whole list was processed by postQuery().
    #
    # On exit, each ticket has t['calc_start'] and t['calc_finish']
    # set (FIXME - we should probably be able to configure those field
    # names.) and can be accessed with TracPM.start() and finish().
    def scheduleTasks(self, options, ticketsByID):
        """Called to schedule tasks"""

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
# FIXME - we should probably have some weird, unique prefix on the
# field names ("pm_", etc.).  Perhaps configurable.
#
# FIXME - do we need access methods for estimate and worked?

class TracPM(Component):
    cfgSection = 'TracPM'
    fields = None

    Option(cfgSection, 'hours_per_estimate', '1', 
           """Hours represented by each unit of estimated work""")
    Option(cfgSection, 'default_estimate', '4.0', 
           """Default work for an unestimated task, same units as estimate""")
    Option(cfgSection, 'estimate_pad', '0.0', 
           "How much work may be remaining when a task goes over estimate,"+
           " same units as estimate""")

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
                                ITaskScheduler, 'CalendarScheduler')

    def __init__(self):
        self.env.log.info('Initializing TracPM')

        # PM-specific data can be retrieved from custom fields or
        # external relations.  self.sources lists all configured data
        # sources and provides a key to self.fields or self.relations
        # to drive the actual db query.
        self.sources = {}

        # All the data sources that may come from custom fields.
        fields = ('percent', 'estimate', 'worked', 'start', 'finish',
                  'pred', 'succ', 'parent')

        # All the data sources that may come from external relations.
        #
        # Each item lists the fields (above) that are affected by this
        # relation.  From configuration we get another three elements:
        # table, src, dst.
        relations = {}
        relations['pred-succ'] = [ 'pred', 'succ' ]

        # Process field configuration
        self.fields = {}
        for field in fields:
            value = self.config.get(self.cfgSection, 'fields.%s' % field)

            # As of 0.11.6, there appears to be a bug in Option() so
            # that a default of None isn't used and we get an empty
            # string instead.
            #
            # Remember the source for this data
            if value != '' and value != None:
                # FUTURE: If we really wanted to, we could validate value
                # against the list of Trac's custom fields.

                self.sources[field] = field
                self.fields[field] = value

        # Process relation configuration
        #
        # Find out how to query ticket relationships
        # Each item is "table,src,dst" so that we can do
        #    SELECT dst FROM table where src = id
        # or
        #    SELECT dst FROM table WHERE src IN origins
        # to find the related tickets.
        self.relations = {}
        for r in relations:
            value = self.config.getlist(self.cfgSection, 'relation.%s' % r)
            # See note above about defaults.
            # Remember the source for this data
            if value != [] and value != None:
                # Validate field and relation configuation
                if len(value) != 3:
                    self.env.log.error('Relation %s is misconfigured. '
                                       'Should have three fields: '
                                       'table,src,dst; found "%s".' % 
                                       (r, value))
                else:
                    for f in relations[r]:
                        if f in self.fields:
                            self.env.log.error('Cannot configure %s as a field '
                                               'and from relation %s' % (f, r))

                        self.sources[f] = r
                    self.relations[r] = relations[r] + value
                    
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
        self.dftEst = float(self.config.get(self.cfgSection, 
                                            'default_estimate'))

        # How much to pad an estimate when a task has run over
        self.estPad = float(self.config.get(self.cfgSection, 'estimate_pad'))

	# Parent format option
	self.parent_format = self.config.get(self.cfgSection,'parent_format')

        # This is the format of start and finish in the Trac database
        self.dbDateFormat = str(self.config.get(self.cfgSection, 'date_format'))


    # Return True if all of the listed PM data items ('pred',
    # 'parent', etc.) have sources configured, False otherwise
    def isCfg(self, sources):
        if type(sources) == type([]):
            for s in sources:
                if s not in self.sources:
                    return False
        else:
            return sources in self.sources

        return True

    def isField(self, field):
        return self.isCfg(field) and self.sources[field] in self.fields

    def isRelation(self, field):
        return self.isCfg(field) and self.sources[field] in self.relations

    # Return True if ticket has a non-empty value for field, False
    # otherwise.
    def isSet(self, ticket, field):
        if self.isCfg(field) \
                and len(ticket[self.fields[field]]) != 0:
            return True
        else:
            return False

    # FIXME - Many of these should be marked as more private.  Perhaps
    # an leading underscore?

    # Parse the start field and return a datetime
    # Return None if the field is not configured or empty.
    def parseStart(self, ticket):
        if self.isSet(ticket, 'start'):
            start = datetime(*time.strptime(ticket[self.fields['start']], 
                                       self.dbDateFormat)[0:7])
            start.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            start = None
        return start

    # Parse the finish field and return a datetime
    # Return None if the field is not configured or empty.
    def parseFinish(self, ticket):
        if self.isSet(ticket, 'finish'):
            finish = datetime(*time.strptime(ticket[self.fields['finish']], 
                                           self.dbDateFormat)[0:7])
            finish.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            finish = None
        return finish

    # Is d at the start of the day
    #
    # It gets messy to do this explicitly inline, especially because
    # some date math seems to have rounding issues that result in
    # non-zero microseconds.
    def isStartOfDay(self, d):
        # Subtract d from midnight that day
        delta = d - d.replace(hour=0, minute=0, second=0, microsecond=0)

        # If within 5 seconds of midnight, it's midnight.
        #
        # Note that seconds and microseconds are always positive
        # http://docs.python.org/library/datetime.html#timedelta-objects
        return  delta.seconds < 5
        

    # Get the value for a PM field from a ticket
    def _fieldValue(self, ticket, field):
        # If the field isn't configured, return None
        if not self.isCfg(field):
            return None
        # If the value comes from a custom field, resolve the field
        # name through sources and use it to index the ticket.
        elif self.isField(field):
            return ticket[self.fields[self.sources[field]]]
        # If the value comes from a relation, we use the internal
        # name directly.
        else:
            return ticket[field]

    # Return the integer ID of the parent ticket
    # 0 if no parent
    # None if parent is not configured
    def parent(self, ticket):
        return self._fieldValue(ticket, 'parent')

    # Return list of integer IDs of children.
    # None if parent is not configured.
    def children(self, ticket):
        return ticket['children']

    # Return a list of integer ticket IDs for immediate precedessors
    # for ticket or an empty list if there are none.
    def predecessors(self, ticket):
        value = self._fieldValue(ticket, 'pred') 
        if value == None:
            return []
        else:
            return value

    # Return a list of integer ticket IDs for immediate successors for
    # ticket or an empty list if there are none.
    def successors(self, ticket):
        value = self._fieldValue(ticket, 'succ')
        if value == None:
            return []
        else:
            return value

    # Return computed start for ticket
    def start(self, ticket):
        return ticket['calc_start'][0]

    # Return computed start for ticket
    def finish(self, ticket):
        return ticket['calc_finish'][0]


    # Return a list of custom fields that PM needs to work.  The
    # caller can add this to the list of fields in a query so that
    # when the tickets are passed back to PM the necessary data is
    # there.
    def queryFields(self):
        fields = []
        for field in self.fields:
            fields.append(self.fields[field])
        return fields

    # Return True if ticket is a milestone, False otherwise.
    def isMilestone(self, ticket):
        return ticket['type'] == self.milestoneType


    # Return total hours of work in ticket as a floating point number
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

    # Return percent complete.  
    # 
    # If estimate and worked are configured and estimate is not 0,
    # returns 'est/work' as a string.
    #
    # If estimate or work are not configured or estimate is 0, returns
    # percent complete as an integer.
    def percentComplete(self, ticket):
        # Closed tickets are 100% complete
        if ticket['status'] == 'closed':
            percent = 100
        # Compute percent complete if given estimate and worked
        elif self.isCfg(['estimate', 'worked']):
            # Try to compute the percent complete, default to 0
            estimate = self.workHours(ticket) / self.hpe
            if (estimate == 0):
                percent = 0
            else:
                worked = ticket[self.fields['worked']]
                if worked == '':
                    percent = 0
                else:
                    worked = float(worked)
                    percent = '%s/%s' % (worked, estimate)
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


    # Returns pipe-delimited, possibily empty string of ticket IDs
    # meeting PM constraints.  Suitable for use as id field in ticket
    # query engine.  
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
            # Query from external table
            if self.isRelation(field):
                relation = self.relations[self.sources[field]]
                # Forward query
                if field == relation[0]:
                    (f1, f2, tbl, src, dst) = relation
                # Reverse query
                elif field == relation[1]:
                    (f1, f2, tbl, dst, src) = relation
                else:
                    raise TracError('Relation configuration error for %s' % 
                                    field)

                # FIXME - is this portable across DBMSs?
                cursor.execute("SELECT %s FROM %s WHERE %s IN (%s)" %
                               (dst, tbl, src,
                                "'" + "','".join(node_list) + "'"))
            # Query from custom field
            elif self.isField(field):
                fieldName = self.fields[self.sources[field]]
                # FIXME - is this portable across DBMSs?
                cursor.execute("SELECT t.id "
                               "FROM ticket AS t "
                               "LEFT OUTER JOIN ticket_custom AS p ON "
                               "    (t.id=p.ticket AND p.name='%s') "
                               "WHERE p.value IN (%s)" % 
                               (fieldName,
                                "'" + "','".join(node_list) + "'"))
            # We really can't get here because the callers test for
            # isCfg() but it's nice form to have an else.
            else:
                raise TracError('Cannot expand %s; '
                                'Not configured as a field or relation.' %
                                field)
                
            nodes = ['%s' % row[0] for row in cursor] 

            return origins + _expand(nodes, field, format)

        id = ''

        if options['root']:
            if not self.isCfg('parent'):
                self.env.log.info('Cannot get tickets under root ' +
                                  'without "parent" field configured')
            else:
                if options['root'] == 'self':
                    if this_ticket:
                        nodes = [ this_ticket ]
                    else:
                        nodes = []
                else:
                    nodes = options['root'].split('|')

                id += '|'.join(_expand(nodes, 
                                       'parent',
                                       self.parent_format))

        if options['goal']:
            if not self.isCfg('succ'):
                self.env.log.info('Cannot get tickets for goal ' +
                                  'without "succ" field configured')
            else:
                if options['goal'] == 'self':
                    if this_ticket:
                        nodes = [ this_ticket ]
                    else:
                        nodes = []
                else:
                    nodes = options['goal'].split('|')

                id += '|'.join(_expand(nodes, 'succ', '%s'))

        return id

    # Create a pseudoticket for a Trac milestone with all the fields
    # needed for PM work.
    def _pseudoTicket(self, id, summary, description, milestone):
        ticket = {}
        ticket['id'] = id
        ticket['summary'] = summary
        ticket['description'] = description
        ticket['milestone'] = milestone

        # Milestones are always shown
        ticket['level'] = 0

        # A milestone has no owner
        ticket['owner'] = ''
        ticket['type'] = self.milestoneType
        ticket['status'] = ''

        if self.isCfg('estimate'):
            ticket[self.fields['estimate']] = 0

        # There is no percent complete for a milestone
        if self.isCfg('percent'):
            ticket[self.fields['percent']] = 0

        # A milestone has no children or parent
        if self.isCfg('parent'):
            ticket[self.fields['parent']] = 0
        ticket['children'] = []

        # Place holder.
        ticket['link'] = ''

        # A milestone has no priority
        ticket['priority'] = 'n/a'

        return ticket

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
                id = id-1
                milestoneTicket = self._pseudoTicket(id, 
                                                     row[0],
                                                     'Milestone %s' % row[0],
                                                     row[0])

                # If there's no due date, let the scheduler set it.
                if self.isCfg('finish'):
                    ts = row[1]
                    if ts:
                        milestoneTicket[self.fields['finish']] = \
                            format_date(ts, self.dbDateFormat)
                    else:
                        milestoneTicket[self.fields['finish']] = ''

                    # jsGantt ignores start for a milestone but we use it
                    # for scheduling.
                    if self.isCfg('start'):
                        milestoneTicket[self.fields['start']] = \
                              milestoneTicket[self.fields['finish']]


                # Any ticket with this as a milestone and no
                # successors has the milestone as a successor
                if self.isCfg(['pred', 'succ']):
                    pred = []
                    for t in tickets:
                        if not t['children'] and \
                                t['milestone'] == row[0] and \
                                self.successors(t) == []:
                            if self.isField('succ'):
                                t[self.fields[self.sources['succ']]] = \
                                    [ id ]
                            else:
                                t['succ'] = [ id ]
                            pred.append(t['id'])
                    if self.isField('pred'):
                        milestoneTicket[self.fields[self.sources['pred']]] = \
                            pred
                    else:
                        milestoneTicket['pred'] = pred

                # A Trac milestone has no successors
                if self.isField('succ'):
                    milestoneTicket[self.fields[self.sources['succ']]] = []
                elif self.isRelation('succ'):
                    milestoneTicket['succ'] = []
                
                tickets.append(milestoneTicket)

    # Process the tickets to normalize formats, etc. to simplify
    # access functions.
    #
    # Also queries PM values that come from external relations.
    #
    # A 'children' field is added to each ticket.  If a 'parent' field
    # is configured for PM, then 'children' is the (possibly empty)
    # list of children.  if there is no 'parent' field, then
    # 'children' is set to None.
    #
    # Milestones for the tickets are added as pseudo-tickets.
    def postQuery(self, options, tickets):
        # Handle custom fields.

        # Clean up custom fields which might be null ('--') vs. blank ('')
        for t in tickets:
            nullable = [ 'pred', 'succ', 
                         'start', 'finish', 
                         'parent', 
                         'worked', 'estimate', 'percent' ]
            for field in nullable:
                if self.isField(field):
                    fieldName = self.fields[self.sources[field]]
                    if fieldName not in t:
                        raise TracError('%s is not a custom ticket field' %
                                        fieldName)
                
                    if t[fieldName] == '--':
                        t[fieldName] = ''

        # Normalize parent field values.  All parent values must be
        # done before building child lists, below.
        if self.isCfg('parent'):
            for t in tickets:
                # ChildTicketsPlugin puts '#' at the start of the
                # parent field.  Strip it for simplicity.
                fieldName = self.fields[self.sources['parent']]
                parent = t[fieldName]
                if len(parent) > 0 and parent[0] == '#':
                    t[fieldName] = parent[1:]

                # An empty parent default to 0 (no such ticket)
                if t[fieldName] == '':
                    t[fieldName] = 0
                # Otherwise, convert the string to an integer
                else:
                    t[fieldName] = int(t[fieldName])
                        
        # Build child lists
        for t in tickets:
            if not self.isCfg('parent'):
                t['children'] = []
            elif self.isField('parent'):
                t['children'] = [c['id'] for c in tickets \
                                     if c[fieldName] == t['id']]

        # Clean up successor, predecessor lists
        for t in tickets:
            lists = [ 'pred', 'succ' ]
            for field in lists:
                if self.isField(field):
                    fieldName = self.fields[self.sources[field]]
                    if t[fieldName] == '':
                        t[fieldName] = []
                    else:
                        t[fieldName] = \
                            [int(s.strip()) \
                                 for s in t[fieldName].split(',')]

        # Fill in relations
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        # Get all the IDs we care about relations from.
        ids = ['%s' % t['id'] for t in tickets]

        # For each configured relation ...
        for r in self.relations:
            # Get the elements of the relationship ...
            (f1, f2, tbl, src, dst) = self.relations[r]
            # FIXME - is this portable across DBMSs?
            idList = "'" + "','".join(ids) + "'"
            # ... query all relations with the desired IDs on either end ...
            cursor.execute("SELECT %s, %s FROM %s "
                           "WHERE %s IN (%s)" 
                           " OR %s IN (%s)" %
                           (src, dst, tbl, src, idList, dst, idList))

            # ... quickly build a local cache of the forward and
            # reverse links ...
            fwd = {}
            rev = {}
            for row in cursor:
                (src, dst) = row
                if dst in fwd:
                    fwd[dst].append(src)
                else:
                    fwd[dst] = [ src ]
                    
                if src in rev:
                    rev[src].append(dst)
                else:
                    rev[src] = [ dst ]

            # ... and put the links in the tickets.
            for t in tickets:
                if t['id'] in fwd:
                    t[f1] = fwd[t['id']]
                else:
                    t[f1] = []
                if t['id'] in rev:
                    t[f2] = rev[t['id']]
                else:
                    t[f2] = []

        self._add_milestones(options, tickets)

    # tickets is an unordered list of tickets.  Each ticket contains
    # at least the fields returned by queryFields() and the whole list
    # was processed by postQuery().  
    def computeSchedule(self, options, tickets):
        # Convert list to dictionary, making copies so schedule can
        # mess with the tickets.
        ticketsByID = {}
        for t in tickets:
            ticketsByID[t['id']] = {}
            for field in t:
                ticketsByID[t['id']][field] = copy.copy(t[field])

        # Schedule the tickets
        self.scheduler.scheduleTasks(options, ticketsByID)

        # Copy back the schedule results
        for t in tickets:
            for field in [ 'calc_start', 'calc_finish']:
                t[field] = ticketsByID[t['id']][field]


# ========================================================================
# Really simple calendar
#
class SimpleCalendar(Component):
    implements(IResourceCalendar)

    def __init__(self):
        self.env.log.debug('Creating a simple calendar')
        """Nothing"""

    # FIXME - we'd like this to honor hoursPerDay
    def hoursAvailable(self, date, resource = None):
        # No hours on weekends
        if date.weekday() > 4:
            hours = 0
        # 8 hours on week days
        else:
            hours = 8.0
        return hours

# ------------------------------------------------------------------------
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
#
# Differs from SimpleScheduler only in using a pluggable calendar to
# determine hours available on a date.
class CalendarScheduler(Component):
    implements(ITaskScheduler)

    pm = None

    def __init__(self):
        # Instantiate the PM component
        self.pm = TracPM(self.env)
        self.cal = SimpleCalendar(self.env)


    # ITaskScheduler method
    # Uses options hoursPerDay and schedule (alap or asap).
    def scheduleTasks(self, options, ticketsByID):
        # fromDate, accounting for working hours and weekends.
        def _calendarOffset(ticket, hours, fromDate):
            if hours < 0:
                sign = -1
            else:
                sign = 1

            delta = timedelta(hours=0)

            while hours != 0:
                f = fromDate + delta

                # Get total hours available for resource on that date
                available = self.cal.hoursAvailable(f, ticket['owner'])

                # Clip available based on time of day on target date
                # (hours before a finish or after a start)
                #
                # Convert 4:30 into 4.5, 16:15 into 16.25, etc.
                h = f.hour + f.minute / 60. + f.second / 3600.

                # See how many hours are available before or after the
                # threshold on this day
                if sign == -1:
                    if h < available:
                        available = h
                else:
                    if options['hoursPerDay']-h < available:
                        available = options['hoursPerDay']-h

                # If we can finish the task this day
                if available >= math.fabs(hours):
                    # See how many hours are available for other tasks this day
                    available += -1 * sign * hours

                    # If there are no more hours this day, make sure
                    # that the delta ends up at the end (start or
                    # finish) of the day
                    if available == 0:
                        if sign == -1:
                            delta += timedelta(hours=-h)
                        else:
                            delta += timedelta(hours=options['hoursPerDay']-h)
                    # If there is time left after this, just update
                    # the delta within this day
                    else:
                        # Add the remaining time to the delta (sign is
                        # implicit in hours)
                        delta += timedelta(hours=hours)

                    # No hours left when we're done.
                    hours = 0
                # If we can't finish the task this day
                else:
                    # We do available hours of work this day ...
                    hours -= sign * available

                    # ... And move to another day to do more.
                    if sign == -1:
                        # Account for the time worked this date
                        # (That is, get to start of the day)
                        delta += timedelta(hours = -h)
                        # Back up to end of previous day
                        delta += timedelta(hours = 
                                           -(24 - options['hoursPerDay']))
                    else:
                        # Account for the time work this date
                        # (That is move to the end of today)
                        delta += timedelta(hours = options['hoursPerDay'] - h)
                        # Move ahead to the start of the next day
                        delta += timedelta(hours = 24 - options['hoursPerDay'])

            return delta

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
                        if pid in ticketsByID:
                            parent = ticketsByID[pid]
                            _schedule_task_alap(parent)
                            if _betterDate(ticketsByID[pid]['calc_finish'],
                                           finish):
                                finish = ticketsByID[pid]['calc_finish']
                        else:
                            self.env.log.info(('Ticket %s has parent %s ' +
                                               'but %s is not in the chart. ' +
                                               'Ancestor deadlines ignored.') %
                                              (t['id'], pid, pid))
                return copy.copy(finish)

            # Find the earliest start of any successor
            # t is a ticket (list of ticket fields)
            # start is a tuple ([date, explicit])
            def _earliest_successor(t, start):
                for id in self.pm.successors(t):
                    if id in ticketsByID:
                        s = _schedule_task_alap(ticketsByID[id])
                        if _betterDate(s, start) and \
                                start == None or \
                                (s and start and s[0] < start[0]):
                            start = s
                    else:
                        self.env.log.info(('Ticket %s has successor %s ' +
                                           'but %s is not in the chart. ' +
                                           'Dependency deadlines ignored.') %
                                          (t['id'], id, id))
                self.env.log.debug('earliest successor is %s' % start)
                return copy.copy(start)

            # If we haven't scheduled this yet, do it now.
            if t.get('calc_finish') == None:
                # If there is a finish set, use it
                if self.pm.isSet(t, 'finish'):
                    # Don't adjust for work week; use the explicit date.
                    finish = self.pm.parseFinish(t)
                    finish += timedelta(hours=options['hoursPerDay'])
                    finish = [finish, True]
                # Otherwise, compute finish from dependencies.
                else:
                    finish = _earliest_successor(t, _ancestor_finish(t))
                    
                    # If dependencies don't give a date, default to
                    # today at close of business
                    if finish == None:
                        # Start at midnight today
                        finish = datetime.today().replace(hour=0, 
                                                          minute=0, 
                                                          second=0, 
                                                          microsecond=0)
                        # Move ahead to beginning of next day so fixup
                        # below will handle work week.
                        finish += timedelta(days=1)

                        finish = [finish, False]

                    # If we are to finish at the beginning of the work
                    # day, our finish is really the end of the previous
                    # work day
                    if self.pm.isStartOfDay(finish[0]):
                        # Start at start of day
                        f = finish[0]
                        # Move back one hour from start of day to make
                        # sure finish is on a work day.
                        f += _calendarOffset(t, -1, f)
                        # Move forward one hour to the end of the day
                        f += timedelta(hours=1)

                        finish[0] = f

                # Set the field
                t['calc_finish'] = finish

            if t.get('calc_start') == None:
                if self.pm.isSet(t, 'start'):
                    start = self.pm.parseStart(t)
                    start = [start, True]
                    # Adjust implicit finish for explicit start
                    if _betterDate(start, finish):
                        hours = self.pm.workHours(t)
                        finish[0] = start[0] + _calendarOffset(t,
                                                               hours,
                                                               start[0])
                        t['calc_finish'] = finish
                else:
                    hours = self.pm.workHours(t)
                    start = t['calc_finish'][0] + \
                        _calendarOffset(t, 
                                        -1*hours, 
                                        t['calc_finish'][0])
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
                        if pid in ticketsByID:
                            parent = ticketsByID[pid]
                            _schedule_task_asap(parent)
                            if _betterDate(ticketsByID[pid]['calc_start'], 
                                           start):
                                start = ticketsByID[pid]['calc_start']
                        else:
                            self.env.log.info(('Ticket %s has parent %s ' +
                                               'but %s is not in the chart. ' +
                                               'Ancestor deadlines ignored.') %
                                              (t['id'], pid, pid))
                return copy.copy(start)

            # Find the latest finish of any predecessor
            # t is a ticket (list of ticket fields)
            # start is a tuple ([date, explicit])
            def _latest_predecessor(t, finish):
                for id in self.pm.predecessors(t):
                    if id in ticketsByID:
                        f = _schedule_task_asap(ticketsByID[id])
                        if _betterDate(f, finish) and \
                                finish == None or \
                                (f and finish and f[0] > finish[0]):
                            finish = f
                    else:
                        self.env.log.info(('Ticket %s has predecessor %s ' +
                                           'but %s is not in the chart. ' +
                                           'Dependency deadlines ignored.') %
                                          (t['id'], id, id))
                return copy.copy(finish)

            # If we haven't scheduled this yet, do it now.
            if t.get('calc_start') == None:
                # If there is a start set, use it
                if self.pm.isSet(t, 'start'):
                    # Don't adjust for work week; use the explicit date.
                    start = self.pm.parseStart(t)
                    start = [start, True]
                # Otherwise, compute start from dependencies.
                else:
                    start = _latest_predecessor(t, _ancestor_start(t))
                    
                    # If dependencies don't give a date, default to today
                    if start == None:
                        # Start at midnight today
                        start = datetime.today().replace(hour=0, 
                                                         minute=0, 
                                                         second=0, 
                                                         microsecond=0)
                        # Move back to end of previous day so fixup
                        # below will handle work week.
                        start += timedelta(days=-1,
                                           hours=options['hoursPerDay'])
                        start = [start, False]

                    # If we are to start at the end of the work
                    # day, our start is really the beginning of the next
                    # work day
                    if self.pm.isStartOfDay(start[0] -
                                            timedelta(hours =
                                                      options['hoursPerDay'])):
                        s = start[0]
                        # Move ahead to the start of the next day
                        s += timedelta(hours=24-options['hoursPerDay'])
                        # Adjust for work days as needed
                        s += _calendarOffset(t, 1, s)
                        s += timedelta(hours=-1)
                        start = [s, start[1]]
                
                # Set the field
                t['calc_start'] = start
                
            if t.get('calc_finish') == None:
                if self.pm.isSet(t, 'finish'):
                    # Don't adjust for work week; use the explicit date.
                    finish = self.pm.parseFinish(t)
                    finish += timedelta(hours=options['hoursPerDay'])
                    finish = [finish, True]
                    # Adjust implicit start for explicit finish
                    if _betterDate(finish, start):
                        hours = self.pm.workHours(t)
                        start[0] = finish[0] + _calendarOffset(t, 
                                                               -1*hours, 
                                                               finish[0])
                        t['calc_start'] = start
                else:
                    hours = self.pm.workHours(t)
                    finish = t['calc_start'][0] + \
                        _calendarOffset(t,
                                        +1*hours,
                                        t['calc_start'][0])
                    finish = [finish, start[1]]
                t['calc_finish'] = finish

            return t['calc_finish']

        # Augment tickets in a scheduler-specific way to make
        # scheduling easier 
        #
        # If a parent task has a dependency, copy it to its children.
        def _augmentTickets(ticketsByID):
            # Indexed by ticket ID, lists ticket's descendants
            desc = {}
            # Build descendant look up recursively.
            def buildDesc(tid):
                # A ticket is in its own "family" tree.
                desc[tid] = [ tid ]
                # For each child, add its subtree.
                for cid in self.pm.children(ticketsByID[tid]):
                    desc[tid] += buildDesc(cid)
                return desc[tid]
            
            # Find the roots of the trees
            roots = []
            for tid in ticketsByID:
                if self.pm.parent(ticketsByID[tid]) == 0:
                    roots.append(tid)

            # Build the descendant tree for each root (and its descendants)
            for tid in roots:
                buildDesc(tid)
                
            # Propagate dependencies from parent to descendants (first
            # children, then recurse).
            # 
            # We don't copy every dependency to every child because
            # several children may form a sequence and thus be
            # affected by the dependency indirectly.  The first child
            # in the sequence gets the parent's predecessors and the
            # last child gets the parent's successors.  Then because
            # of the children's dependence on each other, the parent
            # dependencies affect all the children in the sequence.
            def propagateDependencies(pid):
                parent = ticketsByID[pid]
                # Process predecessors and successors
                for fieldFunc in [ self.pm.predecessors, 
                                   self.pm.successors ]:
                    # Set functions to add dependency and its reverse
                    # between two tickets.
                    fwd = fieldFunc
                    if fwd == self.pm.predecessors:
                        rev = self.pm.successors
                    else:
                        rev = self.pm.predecessors

                    # For each child, if any
                    for cid in self.pm.children(parent):
                        # If the child is in the list we're
                        # working on
                        if cid in ticketsByID:
                            # Does child depend on any "cousins"
                            # (other descendants)?
                            child = ticketsByID[cid]
                            cousins = [did for did in fieldFunc(child) \
                                           if did in desc[pid]]
                            # If not, this is the end of the
                            # line and we have to copy the
                            # parent's dependencies down.
                            if cousins == []:
                                # For each related ticket, if any
                                for tid in fieldFunc(parent):
                                    # If the other ticket is in the list we're
                                    # working on
                                    if tid in ticketsByID:
                                        # Add parent's dependency to this
                                        # child
                                        fwd(ticketsByID[cid]).append(tid)
                                        rev(ticketsByID[tid]).append(cid)

                            # Recurse to lower-level descendants
                            propagateDependencies(cid)


            # For each ticket to schedule
            for tid in ticketsByID:
                # If it has no parent
                if self.pm.parent(ticketsByID[tid]) == 0:
                    # Propagate depedencies down to its children
                    # (which recurses to update other descendants)
                    propagateDependencies(tid)

        # Main schedule processing

        # If there is a parent/child relationship configured
        if self.pm.isCfg('parent'):
            _augmentTickets(ticketsByID)

        for id in ticketsByID:
            if options['schedule'] == 'alap':
                _schedule_task_alap(ticketsByID[id])
            else:
                _schedule_task_asap(ticketsByID[id])

