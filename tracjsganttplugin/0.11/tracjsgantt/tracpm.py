import re
import time
import math
import copy
from datetime import timedelta, datetime

from trac.util.datefmt import format_date, to_utimestamp, localtz, to_datetime
from trac.ticket import ITicketChangeListener, Ticket
from trac.ticket.query import Query

from trac.config import IntOption, Option, ExtensionOption
from trac.core import implements, Component, TracError, Interface, ExtensionPoint
from trac.env import IEnvironmentSetupParticipant
from trac.db import DatabaseManager

from pmapi import IResourceCalendar, ITaskScheduler, ITaskSorter

import db_default

# TracPM masks implementation details of how various plugins implement
# dates and ticket relationships and business rules about what the
# default estimate for a ticket is, etc.
#
# TracPM.query() augments TicketQuery so that you can find all the
# descendants of a ticket (root=id) or all the tickets required for a
# specified ticket (goal=id).  After querying, TracPM post-processes
# the query results to augment the tickets in memory with normalized
# meta-data about their relationships.  After that processing, a
# ticket may have the properties listed below.  (Which properties are
# present depends on what is configured in the [TracPM] section of
# trac.ini.)
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
#
#
# Some notes on terminology
#
# goal
#
# There is potential confusion about what a "milestone" is.  In
# Project Management terms, a milestone is a due date for a
# deliverable.  In Trac, a milestone is more like a project: a set of
# tickets and an optional date when those tickets are due.  To avoid
# confusion (or excessive use of adjectives leading to variables like
# pmMilestone and tracMiletone, etc.) TracPM uses the term "goal."
#
# A goal may be an instance of a user-specific ticket type (e.g.,
# "goal", "inchpebble", "milestone") or a pseudo-ticket representing a
# Trac milestone.
#
# A Trac milestone may be complete or incomplete.  The goal
# pseudo-ticket for a Trac milestone has a status of "closed" if the
# milestone has a completed date or a configurable open status if not
# yet completed.
#
# The tickets required for a goal are scheduled if the goal has a status
# in a configurable list of active goal statuses (or if the list is
# empty).


class TracPM(Component):
    implements(IEnvironmentSetupParticipant)

    cfgSection = 'TracPM'


    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        self.log.info('Creating environment for TracPM.')
        self.found_db_version = 0
        self.upgrade_environment(self.env.get_db_ctx())


    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute('SELECT value FROM system WHERE name=%s',
                       (db_default.name, ))
        value = cursor.fetchone()
        try:
            self.found_db_version = int(value[0])
            if self.found_db_version < db_default.version:
                self.log.info('TracPM environment out of date.')
                return True
        except:
            self.log.info('TracPM environement missing.')
            self.found_db_version = 0
            return True

        # Environment version is current
        return False


    def upgrade_environment(self, db):
        self.log.info('Upgrading environment for TracPM.')
        db_manager, _ = DatabaseManager(self.env)._get_connector()
        cursor = db.cursor()

        # Add or update TracPM version in system table
        if not self.found_db_version:
            cursor.execute("INSERT INTO system (name, value) VALUES (%s, %s)",
                           (db_default.name, db_default.version))
        else:
            cursor.execute("UPDATE system SET value=%s WHERE name=%s",
                           (db_default.version, db_default.name))

        # Create tables
        for table in db_default.tables:
            for sql in db_manager.to_sql(table):
                cursor.execute(sql)


    # Configurable data sources
    fields = None
    sources = None
    relations = None
    # How dates are stored in the database
    dbDateFormat = None
    # What ticket type to treat like milestones
    milestoneType = None
    # Configurable estimate pad, default estimate, hours per estimate
    estPad = None
    dftEst = None
    hpe = None
    # Format of parent field (e.g., with or without leading '#')
    parent_format = None


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
    Option(cfgSection, 'milestone_type', '*deprecated*', 
           """Ticket type for milestone-like tickets (Deprecated; use goal_ticket_type.)""")
    Option(cfgSection, 'goal_ticket_type', 'milestone', 
           """Ticket type for milestone-like tickets""")
    Option(cfgSection, 'incomplete_milestone_goal_status', 'active', 
           """Status to give goal-type tickets representing incomplete Trac milestones""")
    Option(cfgSection, 'active_goal_statuses', 'active', 
           """List of statuses for goal-type tickets that are active""")
    Option(cfgSection, 'useActuals', '0',
           """Use actual start, finish date for tickets""")

    scheduler = ExtensionOption(cfgSection, 'scheduler', 
                                ITaskScheduler, 'ResourceScheduler')

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
        relations['parent-child'] = [ 'parent', 'children' ]

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

        # Tickets of this type will be treated as goals
        self.goalTicketType = self.config.get(self.cfgSection, 'milestone_type')
        if self.goalTicketType == '*deprecated*':
            self.goalTicketType = self.config.get(self.cfgSection, 
                                                  'goal_ticket_type')
        else:
            self.env.log.info('The milestone_type setting is deprecated.'
                              ' Use goal_ticket_type.')

        # Goal-type tickets with these statuses will be considered active.
        # (An empty list bypasses the test for active.)
        self.activeGoalStatuses = self.config.getlist(self.cfgSection,
                                                      'active_goal_statuses')

        # An open goal-type pseudo-ticket representing a Trac
        # milestone has this status. (Closed milestones will have
        # status of "closed".)
        self.incompleteMilestoneStatus = \
            self.config.get(self.cfgSection,
                            'incomplete_milestone_goal_status')

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

        # Use actual start, finish time for tickets
        self.useActuals = int(self.config.get(self.cfgSection, 'useActuals'))

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

    def parseDbDate(self, dateString):
        if not dateString:
            d = None
        else:
            d = datetime(*time.strptime(dateString, 
                                        self.dbDateFormat)[0:7])
            d = d.replace(hour=0, minute=0, second=0, microsecond=0, 
                          tzinfo=localtz)
        return d

    # Parse the start field and return a datetime
    # Return None if the field is not configured or empty.
    def parseStart(self, ticket):
        if self.isSet(ticket, 'start'):
            try:
                start = self.parseDbDate(ticket[self.fields['start']])
            except:
                raise TracError('Ticket %s has an invalid %s value, "%s".' \
                                    ' It should match the format "%s".' %
                                (ticket['id'], 
                                 self.fields['start'],
                                 ticket[self.fields['start']],
                                 self.dbDateFormat))
        else:
            start = None
        return start

    # Parse the finish field and return a datetime
    # Return None if the field is not configured or empty.
    def parseFinish(self, ticket):
        if self.isSet(ticket, 'finish'):
            try:
                finish = self.parseDbDate(ticket[self.fields['finish']]) 
            except:
                raise TracError('Ticket %s has an invalid %s value, "%s".' \
                                    ' It should match the format "%s".' %
                                (ticket['id'], 
                                 self.fields['finish'],
                                 ticket[self.fields['finish']],
                                 self.dbDateFormat))
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
        delta = d - d.replace(hour=0, minute=0, second=0, microsecond=0,
                              tzinfo=localtz)

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
    # None if no parent or parent is not configured
    def parent(self, ticket):
        value = self._fieldValue(ticket, 'parent')
        if value == None:
            return value
        elif value == []:
            return None
        else:
            return value[0]

    # Return list of integer IDs of children.
    # None if parent is not configured.
    def children(self, ticket):
        return ticket['children']

    # Return an unordered list of integer IDs of the roots (tickets
    # without parents) in ticketsByID.
    def roots(self, ticketsByID):
        if self.isCfg('parent'):
            roots = []
            # Find the roots of the trees
            for tid in ticketsByID:
                pid = self.parent(ticketsByID[tid])
                if not pid or pid not in ticketsByID:
                    roots.append(tid)
        # If there is no parent field, all tickets are roots.
        else:
            roots = ticketsByID.keys()

        return roots

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

    # Return start for ticket as a Python datetime object
    def start(self, ticket):
        if ticket.get('_calc_start'):
            return ticket['_calc_start'][0]
        elif ticket.get('_sched_start'):
            return to_datetime(ticket['_sched_start'])
        else:
            return None

    # Return finish for ticket as a Python datetime object
    def finish(self, ticket):
        if ticket.get('_calc_finish'):
            return ticket['_calc_finish'][0]
        elif ticket.get('_sched_finish'):
            return to_datetime(ticket['_sched_finish'])
        else:
            return None

    # Return a set of custom fields that PM needs to work.  The
    # caller can add this to the list of fields in a query so that
    # when the tickets are passed back to PM the necessary data is
    # there.
    def queryFields(self):
        # Start with Trac core fields related to PM/scheduling
        fields = set([ 'owner', 'status', 'milestone', 'priority', 'type' ])
        # Add configured custom fields for dependendencies, etc.
        for field in self.fields:
            fields.add(self.fields[field])
        return fields

    # Return True if ticket is a milestone, False otherwise.
    def isMilestone(self, ticket):
        return ticket['type'] == self.goalTicketType

    # Return True if ticket is a Trac milestone, False otherwise.
    def isTracMilestone(self, ticket):
        return self.isMilestone(ticket) and ticket['id'] < 0


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
        if ticket['type'] == self.goalTicketType:
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

    # Find all the tasks connected (directly or indirectly) to the
    # specified origins via dependencies (parent-child or pred-succ).
    #
    # We expand a border between tasks we have explored and those yet
    # to explore until there are no more to explore.  This is a
    # variation on a graph coloring algorithm which colors explored
    # nodes black, border nodes grey, and nodes to explore white.
    # Such labeling doesn't fit well with the Trac database structure.
    # We could name our sets white, grey, and black, but that's much
    # less clear than naming them for what they contain.
    #
    # @param origins list of integer ticket IDs to fan out from
    # @param depth how how many times to traverse links (-1=all, default)
    # @return list of ticket ID strings for tickets reachable from
    #   origins (including origins)
    def _reachable(self, origins, depth=-1):
        # Helper to find the immediate neighbors of a set of nodes.
        # @param nodes a set of nodes to find neighbors of
        def neighbors(nodes):
            n = set()
            nodes = list(nodes)
            # Get parents of nodes
            if self.isCfg('parent'):
                n |= set(self._followLink(nodes,
                                         'parent', 
                                         self.parent_format, 
                                         1))
            # Get children of nodes
            if self.isRelation('parent'):
                n |= set(self._followLink(nodes,
                                         'children',
                                         '%s',
                                         1))
            # Get immediate predecessors of nodes
            if self.isCfg('pred'):
                n |= set(self._followLink(nodes,
                                         'pred',
                                         '%s',
                                         1))
            # Get immedicate successors of nodes
            if self.isCfg('succ'):
                n |= set(self._followLink(nodes,
                                         'succ',
                                         '%s',
                                         1))

            return n

        # We haven't explored anything yet.
        explored = set()
        # We'll explore out from the initial set
        toExplore = set(origins)
        # While we have more exploring to do
        while toExplore != set() and depth != 0:
            depth -= 1
            # Our border is what we're about to explore
            border = toExplore
            # Find neighbors of the border nodes
            toExplore = neighbors(border)
            # Some of the neighbors of the border are already in the
            # explored set.  Remove them.
            toExplore -= explored
            # Now we've explored the border
            explored |= border

        return list(explored)


    # Expand the list of tickets in origins to include those
    # related through field.
    # 
    # Recurses following link until 
    #  * no new items are found, or
    #  * field has been followed depth times
    # 
    # @param origins a list of ticket IDs as strings
    # @param field the field to follow
    # @param format the format of ticket IDs in field
    # @param depth how many steps to follow the link (default -1, no limit)
    #
    # @return a list of integer ticket IDs of tickets up to depth
    # steps from origins via field
    def _followLink(self, origins, field, format, depth = -1):
        if len(origins) == 0 or depth == 0:
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

            # Build up enough instances of %s to represent all the
            # nodes.  The DB API will replace them with items from
            # node_list, properly quoted for the DB back-end.
            #
            # In 0.12, we could do
            #
            #   ','.join([db.quote(node) for node in node_list])
            #
            # but 0.11 doesn't have db.quote()
            inClause = "IN (%s)" % ','.join(('%s',) * len(node_list))
            cursor.execute("SELECT %s FROM %s WHERE %s " % \
                               (dst, tbl, src) + \
                               inClause,
                           node_list)
        # Query from custom field
        elif self.isField(field):
            fieldName = self.fields[self.sources[field]]
            # See explantion in relation handling, above.
            inClause = "IN (%s)" % ','.join(('%s',) * len(node_list))
            cursor.execute("SELECT t.id "
                           "FROM ticket AS t "
                           "LEFT OUTER JOIN ticket_custom AS p ON "
                           "    (t.id=p.ticket AND p.name=%s) "
                           "WHERE p.value " + inClause,
                           [fieldName] + node_list)
        # We really can't get here because the callers test for
        # isCfg() but it's nice form to have an else.
        else:
            raise TracError('Cannot expand %s; '
                            'Not configured as a field or relation.' %
                            field)

        # Get tickets IDs of related tickets as strings
        nodes = ['%s' % row[0] for row in cursor] 
        # Filter out ticket IDs we already know about
        nodes = [tid for tid in nodes if tid not in origins]

        return nodes + self._followLink(nodes, field, format, depth - 1)


    # Returns (possibily empty) set of ID strings of tickets
    # meeting PM constraints.
    # FIXME - dumb name
    def preQuery(self, options, req = None):
        ids = set()

        this_ticket = None
        if req:
            matches = re.match('/ticket/(\d+)', req.path_info)
            if matches:
                this_ticket = matches.group(1)

        if options.get('scheduled'):
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT ticket FROM schedule")
            for row in cursor:
                tid = row[0]
                ids.add(str(tid))

        if options.get('root'):
            if not self.isCfg('parent'):
                self.env.log.info('Cannot get tickets under root ' +
                                  'without "parent" field configured')
            else:
                nodes = set()
                if options['root'] == 'self':
                    if this_ticket:
                        nodes.add(this_ticket)
                    else:
                        # FIXME - display an error here that self needs a ticket
                        pass
                else:
                    nodes |= set(options['root'].split('|'))

                ids |= nodes
                ids |= set(self._followLink(nodes, 
                                            'parent', 
                                            self.parent_format))

        if options.get('goal'):
            if not self.isCfg('succ'):
                self.env.log.info('Cannot get tickets for goal ' +
                                  'without "succ" field configured')
            else:
                nodes = set()
                if options['goal'] == 'self':
                    if this_ticket:
                        nodes.add(this_ticket)
                    else:
                        # FIXME - display an error here that self needs a ticket
                        pass
                else:
                    nodes |= set(options['goal'].split('|'))

                # Loop getting all the predecessors of the tickets
                # gathered so far then the children of the tickets
                # gathered so far until the list doesn't change with a
                # new query.
                nodes2 = set()
                while nodes != nodes2:
                    # Get all the predecessors
                    nodes2 = nodes | set(self._followLink(nodes, 'succ', '%s'))

                    # Get the children, if parent configured
                    if self.isCfg('parent'):
                        nodes = nodes2 | set(self._followLink(nodes2, 
                                                              'parent', 
                                                              self.parent_format))
                    else:
                        nodes = nodes2

                ids |= nodes

        return ids

    # Create a pseudoticket for a Trac milestone with all the fields
    # needed for PM work.
    def _pseudoTicket(self, tid, summary, description, milestone):
        ticket = {}
        ticket['id'] = tid
        ticket['summary'] = summary
        ticket['description'] = description
        ticket['milestone'] = milestone

        # Milestones are always shown
        ticket['level'] = 0

        # A milestone has no owner
        ticket['owner'] = ''
        ticket['type'] = self.goalTicketType
        ticket['status'] = ''

        if self.isCfg('estimate'):
            ticket[self.fields['estimate']] = 0

        if self.isCfg('worked'):
            ticket[self.fields['worked']] = 0

        # There is no percent complete for a pseudoticket
        if self.isCfg('percent'):
            ticket[self.fields['percent']] = 0

        # A milestone has no children or parent
        if self.isField('parent'):
            ticket[self.fields['parent']] = [ ]
        else:
            ticket['parent'] = [ ]
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

        for t in tickets:
            if 'milestone' in t and \
                    t['milestone'] != '' and \
                    t['milestone'] not in milestones:
                milestones.append(t['milestone'])

        # Need a unique ID for each task.
        if len(milestones) > 0:
            tid = 0

            # Get the milestones and their due dates
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            # See explanation in _followLink()
            inClause = "IN (%s)" % ','.join(('%s',) * len(milestones))
            cursor.execute("SELECT name, due, completed FROM milestone " +
                           "WHERE name " + inClause,
                           milestones)
            for row in cursor:
                msName, msDueDate, msCompletedDate = row

                tid = tid - 1
                milestoneTicket = self._pseudoTicket(tid, 
                                                     msName,
                                                     'Milestone %s' % msName,
                                                     msName)

                # If the completed date is set (non-0), the milestone is closed"
                if msCompletedDate:
                    milestoneTicket['status'] = 'closed'
                # Otherwise, use the configured open status
                else:
                    milestoneTicket['status'] = self.incompleteMilestoneStatus

                # If there's no due date, let the scheduler set it.
                if self.isCfg('finish'):
                    ts = msDueDate
                    if ts:
                        # The scheduled start and finish, from the database
                        milestoneTicket['_sched_start'] = ts
                        milestoneTicket['_sched_finish'] = ts

                        milestoneTicket[self.fields['finish']] = \
                            format_date(ts, self.dbDateFormat)
                    else:
                        milestoneTicket[self.fields['finish']] = ''

                    # jsGantt ignores start for a milestone but we use it
                    # for scheduling.
                    if self.isCfg('start'):
                        milestoneTicket[self.fields['start']] = \
                              milestoneTicket[self.fields['finish']]
                elif self.isCfg('start'):
                    milestoneTicket[self.fields['start']] = ''

                # Any ticket with this as a milestone and no
                # successors has the milestone as a successor
                if self.isCfg(['pred', 'succ']):
                    pred = []
                    for t in tickets:
                        if t['milestone'] == msName and \
                                self.successors(t) == []:
                            if self.isField('succ'):
                                t[self.fields[self.sources['succ']]] = \
                                    [ tid ]
                            else:
                                t['succ'] = [ tid ]
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

    # Get ticket dates from the database.
    #
    # On exit:
    #  * Tickets with a precomputed schedule have _sched_start and
    #    _sched_finish populated from the database.
    #
    #  * Active tickets (in a state other than "new") have
    #    _actual_start set to the time of the first transition out of
    #    "new"
    #
    #  * Closed tickets (those in the "closed" state) have
    #    _actual_finish set from the last transition into "closed".
    def getTicketDates(self, tickets):
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Table indexed by ticket ID for faster updates
        ticketsByID = {}
        for t in tickets:
            ticketsByID[t['id']] = t

        # All the tickets we care about.
        ids = ticketsByID.keys()

        # Get dates from precomputed schedule, if any.
        inClause = "IN (%s)" % ','.join(('%s',) * len(ids))
        cursor.execute("SELECT ticket, start, finish" +
                       " FROM schedule WHERE ticket " +
                       inClause,
                       ids)
        for row in cursor:
            tid, start, finish = row
            ticketsByID[tid]['_sched_start'] = start
            ticketsByID[tid]['_sched_finish'] = finish

        # Get actual start for active tickets. (Don't do this for
        # milestones.)
        taskIDs = [t['id'] for t in tickets if not self.isMilestone(t)]
        if len(taskIDs) > 0:
            inClause = "IN (%s)" % ','.join(('%s',) * len(taskIDs))
            cursor.execute("SELECT id, x.time AS begunTime" +
                           " FROM ticket" + 
                           " INNER JOIN ticket_change AS x" + 
                           "     ON (x.ticket = ticket.id AND x.field = %s)" + 
                           " WHERE x.time = (SELECT MIN(time)" + 
                           "                 FROM ticket_change AS y" + 
                           "                 WHERE y.ticket = ticket.id " + 
                           "                     AND y.field = %s" + 
                           "                 GROUP BY y.ticket)" + 
                           "     AND x.oldvalue = %s " + 
                           "     AND ticket.id " + 
                           inClause,
                           ['status', 'status', 'new'] + taskIDs)
            for row in cursor:
                (tid, begunTime) = row
                ticketsByID[tid]['_actual_start'] = begunTime


        # Get actual finish for closed tickets.
        # FIXME - omit milestone as above?
        closedIDs = [t['id'] for t in tickets if t['status'] == 'closed']
        if len(closedIDs) > 0:
            inClause = "IN (%s)" % ','.join(('%s',) * len(closedIDs))
            cursor.execute("SELECT id, x.time AS closedTime" + 
                           " FROM ticket" + 
                           " INNER JOIN ticket_change AS x" + 
                           "     ON (x.ticket = ticket.id AND x.field = %s)" + 
                           " WHERE x.time = (SELECT MAX(time)" + 
                           "                 FROM ticket_change AS y" + 
                           "                 WHERE y.ticket = ticket.id " + 
                           "                     AND y.field = %s" + 
                           "                 GROUP BY y.ticket)" + 
                           "     AND x.newvalue = %s " + 
                           "     AND ticket.id " + 
                           inClause,
                           ['status', 'status', 'closed'] + closedIDs)
            for row in cursor:
                (tid, closedTime) = row
                ticketsByID[tid]['_actual_finish'] = closedTime


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
    # Schedule information comes from the TracPM private table schedule.
    #
    # Any "dangling references" are cleaned up.  That is, if A is a
    # parent of B but A is not in tickets then the returned set shows
    # B with no parent.  Similarly for predecessors and successors.
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

        # Get all the IDs we care about
        ids = [t['id'] for t in tickets]

        # Normalize parent field values.  All parent values must be
        # done before building child lists, below.
        if self.isField('parent'):
            for t in tickets:
                # ChildTicketsPlugin puts '#' at the start of the
                # parent field.  Strip it for simplicity.
                fieldName = self.fields[self.sources['parent']]
                parent = t[fieldName]
                if len(parent) > 0 and parent[0] == '#':
                    t[fieldName] = parent[1:]

                # An empty parent field string, default empty list (no parent)
                if t[fieldName] == '':
                    t[fieldName] = []
                # If the parent isn't in the list we're processing,
                # pretend there is no parent.
                elif int(t[fieldName]) not in ids:
                    t[fieldName] = []
                # Otherwise, convert the string to an integer and put
                # it in a list.
                #
                # NOTE: Subtickets plugin allows multiple parents.
                # The parent field is then in the form "123, 234". In
                # that case, the int() call will raise an exception
                # and the overall query will crash.  To fail
                # gracefully, we'd have to use a try around the
                # parsing (which would add overhead on every call that
                # almost never provided any benefit because there is
                # usually no exception to catch), use a regular
                # expression to look for non-digit characters (again,
                # expensive) or split the string (which works for
                # Subtickets but may not handle another plugin which
                # uses a different separator).  I choose to let the
                # exception be unhandled.
                else:
                    t[fieldName] = [ int(t[fieldName]) ]

        # Build child lists
        for t in tickets:
            if not self.isCfg('parent'):
                t['children'] = []
            # NOTE: This can't build dangling references becuase it is
            # built from the parent field which is set to None, above,
            # if the parent isn't in the set we're processing.
            elif self.isField('parent'):
                fieldName = self.fields[self.sources['parent']]
                t['children'] = [c['id'] for c in tickets \
                                     if t['id'] in c[fieldName]]

        # Clean up successor, predecessor lists
        for t in tickets:
            lists = [ 'pred', 'succ' ]
            for field in lists:
                if self.isField(field):
                    fieldName = self.fields[self.sources[field]]
                    if t[fieldName] == '':
                        t[fieldName] = []
                    else:
                        # Get all the related tickets
                        t[fieldName] = \
                            [int(s.strip()) \
                                 for s in t[fieldName].split(',')]
                        # Prune the list to tickets we care about
                        t[fieldName] = [tid for tid in t[fieldName] \
                                            if tid in ids]

        # Fill in relations
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # For each configured relation ...
        for r in self.relations:
            # Get the elements of the relationship ...
            (f1, f2, tbl, src, dst) = self.relations[r]
            # ... query all relations with the desired IDs on either end ...
            # See explanation in _followLink()
            inClause = "IN (%s)" % ','.join(('%s',) * len(ids))
            # Use AND, not OR, here so we only get links between the
            # tickets were care about and don't create dangling
            # references.
            cursor.execute("SELECT %s, %s FROM %s " % (src, dst, tbl) + \
                               "WHERE %s " % src + inClause + \
                               " AND %s " % dst + inClause,
                           ids + ids)

            # ... quickly build a local cache of the forward and
            # reverse links (where both ends are in the list we care
            # about) ...
            fwd = {}
            rev = {}
            for row in cursor:
                # FIXME - this masks src, dst field names above.
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

        # Get precomputed schedule, close dates, etc.
        self.getTicketDates(tickets)

        # Add pseudo-tickets for Trac milestones
        self._add_milestones(options, tickets)

    # Something like ticket.query.Query() with a slightly different
    # interface.
    # 
    # @param options hash of query options (e.g., id, milestone, owner)
    # @param fields set of names of fields that the caller needs
    #     (e.g., 'status')
    # @param ticket ticket to use for "root=this", "goal=this".
    #
    # @return a list of ticket results, each item is a hash of ticket
    #   fields including those named in fields and those required for PM
    #
    def query(self, options, fields, req=None):
        query_args = {}
        # Copy query args from caller (e.g., q_a['owner'] = 'monty|phred')
        for key in options.keys():
            # FIXME - This test is a kludge.  Need a way to exclude
            # those handled by preQuery() in a data-driven way.
            if key not in [ 'goal', 'root', 
                            'start', 'finish', 
                            'useActuals', 'scheduled' ]:
                query_args[str(key)] = options[key]

        # Expand (or set) list of IDs to include those specified by PM
        # query meta-options (e.g., root)
        pm_ids = self.preQuery(options, req)
        if len(pm_ids) != 0:
            if 'id' in query_args:
                query_args['id'] += '|' + '|'.join(pm_ids)
            else:
                query_args['id'] = '|'.join(pm_ids)

        # Default to getting all tickets
        if 'max' not in query_args:
            quary_args['max'] = 0

        # Tell the query what columns to return
        query_args['col'] = "|".join(self.queryFields() | fields)

        # Construct the querystring. 
        query_string = '&'.join(['%s=%s' % 
                                 (str(f), unicode(v)) for (f, v) in 
                                 query_args.iteritems()]) 

        # Get the Query object. 
        query = Query.from_string(self.env, query_string)

        # Get all tickets
        tickets = query.execute(req)

        # Post process to add more PM stuff
        self.postQuery(options, tickets)

        return tickets

    # tickets is an unordered list of tickets as returned by TracPM.query().
    #
    # TracPM.query() preloads schedule data from the database, if present.
    # 
    # If options['force'] is True, the precomputed schedule values are
    # ignored and every ticket is rescheduled.
    #
    # If options['force'] is False or missing, the precomputed
    # schedule values are preserved and tickets without precomputed
    # schedule values are scheduled around those times.
    def computeSchedule(self, options, tickets):
        # Convert list to dictionary, making copies so schedule can
        # mess with the tickets.
        ticketsByID = {}
        for t in tickets:
            ticketsByID[t['id']] = {}
            for field in t:
                ticketsByID[t['id']][field] = copy.copy(t[field])

        # Normalize useActuals from a wiki macro '1' vs. '0' (or
        # absent) to a Boolean
        if options.get('useActuals'):
            if options['useActuals'] == '1':
                options['useActuals'] = True
            else:
                options['useActuals'] = False
        elif self.useActuals == 1:
            options['useActuals'] = True
        else:
            options['useActuals'] = False

        # Schedule the tickets
        self.scheduler.scheduleTasks(options, ticketsByID)

        # Copy back the schedule results
        for t in tickets:
            for field in [ '_calc_start', '_calc_finish']:
                if field in ticketsByID[t['id']]:
                    t[field] = ticketsByID[t['id']][field]

    # Recompute schedule 
    #
    # Compute schedule, like computeSchedule(), but on return each
    # ticket has a "_rescheduled" field if its schedule changed.  
    def recomputeSchedule(self, options, tickets):
        # Call computeSchedule
        self.computeSchedule(options, tickets)

        # Test each returned ticket to see if the start or finish changed
        for t in tickets:
            dbStart = t.get('_sched_start')
            dbFinish = t.get('_sched_finish')
            if not dbStart:
                rescheduled = True
            elif dbStart != to_utimestamp(self.start(t)):
                rescheduled = True
            elif not dbFinish:
                rescheduled = True
            elif dbFinish != to_utimestamp(self.finish(t)):
                rescheduled = True
            else:
                rescheduled = False

            t['_rescheduled'] = rescheduled


    # Augment tickets by propagating dependencies from parents to
    # children
    #
    # We don't copy every dependency to every child because several
    # children may form a sequence and thus be affected by the
    # dependency indirectly.  The first child in the sequence gets the
    # parent's predecessors and the last child gets the parent's
    # successors.  Then because of the children's dependence on each
    # other, the parent dependencies affect all the children in the
    # sequence.

    # FIXME - I don't like this name.  It really just propagates
    # dependencies but that's the name of the private helper defined
    # inside this function.  What can I call the helper?
    def augmentTickets(self, ticketsByID):
        # Indexed by ticket ID, lists ticket's descendants
        desc = {}
        # Build descendant look up recursively.
        def buildDesc(tid):
            # A ticket is in its own "family" tree.
            desc[tid] = [ tid ]
            # For each child, add its subtree.
            for cid in self.children(ticketsByID[tid]):
                desc[tid] += buildDesc(cid)
            return desc[tid]

        # Propagate dependencies from parent to descendants (first
        # children, then recurse).
        # 
        def propagateDependencies(pid):
            parent = ticketsByID[pid]
            # Process predecessors and successors
            for fieldFunc in [ self.predecessors, 
                               self.successors ]:
                # Set functions to add dependency and its reverse
                # between two tickets.
                fwd = fieldFunc
                if fwd == self.predecessors:
                    rev = self.successors
                else:
                    rev = self.predecessors

                # For each child, if any
                for cid in self.children(parent):
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
                            for tid in fwd(parent):
                                # If the other ticket is in the list we're
                                # working on
                                if tid in ticketsByID:
                                    # And not already linked
                                    if tid not in fwd(ticketsByID[cid]):
                                        # Add parent's dependency to this
                                        # child
                                        fwd(ticketsByID[cid]).append(tid)
                                        rev(ticketsByID[tid]).append(cid)

                        # Recurse to lower-level descendants
                        propagateDependencies(cid)


        roots = self.roots(ticketsByID)
        if self.isCfg('parent'):
            # Build the descendant tree for each root (and its descendants)
            for tid in roots:
                buildDesc(tid)

        # For each ticket
        for tid in ticketsByID:
            ticket = ticketsByID[tid]
            # If it is the root of a tree
            if tid in roots:
                # Propagate depedencies down to its children
                # (which recurses to update other descendants)
                propagateDependencies(tid)

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
# Some common behaviors for task sorters.
class BaseSorter:
    # When sorting on an enum like priority or severity, we need to
    # sort on 1, 2, 3, not 'critical', 'blocker', 'major', etc.
    def _buildEnumMap(self, field):
        classMap = {}
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT name," + 
                       db.cast('value', 'int') + 
                       " FROM enum WHERE type=%s", (field,))
        for name, value in cursor:
            classMap[name] = value

        return classMap

    # Priorities are continuous, 0..n, so half the length is average
    # value Search for the priority string that has that value.
    def averageEnum(self, enumMap):
        n = len(enumMap) / 2
        # Search for the priority string that has that value
        avgValue = None
        for value in enumMap:
            if enumMap[value] == n:
                avgValue = value
        # If we didn't find one (unlikely), just use the first.
        if avgValue == None:
            avgValue = enumMap.keys()[0]

        return avgValue

    # Compare two tasks by a single field.
    def compareOneField(self, field, t1, t2):
        p1 = t1[field]
        p2 = t2[field]
        # Better priority (lower number) earlier
        if p1 < p2:
            result = -1
        elif p1 > p2:
            result = 1
        else:
            result = 0
        return result

# ------------------------------------------------------------------------
class SimpleSorter(BaseSorter, Component):
    implements(ITaskSorter)

    prioMap = None

    def __init__(self):
        self.prioMap = self._buildEnumMap('priority')

    # Make sure all tickets hav a valid priority that we can map to
    # sortable integer.
    def prepareTasks(self, ticketsByID):
        # Use average priority for tickets with bad priority
        avgPriority = self.averageEnum(self.prioMap)

        # Process all the tickets
        for tid in ticketsByID:
            ticket = ticketsByID[tid]
            if self.prioMap.get(ticket['priority']) == None:
                ticket['priority'] = avgPriority

    # Compare two tickets by their priority value.
    def compareTasks(self, t1, t2):
        return self.compareOneField('priority', t1, t2)

# ------------------------------------------------------------------------
# Sort tasks within a "project".  That is, using some grouping type
# ticket using Subtickets or ChildTickets plugin to create a tree of
# projects made of deliverables which have tasks which have subtasks,
# etc. and being able to adjust leaf-node task priority by changing
# the project priority and having it carry through the tree.
class ProjectSorter(BaseSorter, Component):
    implements(ITaskSorter)

    pm = None

    prioMap = None

    def __init__(self):
        self.prioMap = self._buildEnumMap('priority')
        # FIXME - would I be better off having the PM pass itself in
        # when creating the sorter?
        self.pm = TracPM(self.env)

    # Make sure all tickets hav a valid priority that we can map to
    # sortable integer and compute effective priority of children
    # based on parent priority.
    def prepareTasks(self, ticketsByID):
        # Make sure every ticket has a valid priority.

        # Use average priority for tickets with bad priority
        avgPriority = self.averageEnum(self.prioMap)

        # Process all the tickets
        for tid in ticketsByID:
            ticket = ticketsByID[tid]
            if self.prioMap.get(ticket['priority']) == None:
                ticket['priority'] = avgPriority

        def setEffectivePriority(tid, parentPriority):
            ticket = ticketsByID[tid]
            effectivePriority = parentPriority + \
                [ self.prioMap[ticket['priority']] ]
            ticket['effectivePriority'] = copy.copy(effectivePriority)
            for cid in self.pm.children(ticket):
                setEffectivePriority(cid, effectivePriority)

        # Build up "effective priority" by prepending parent priority
        # to task priority.
        for pid in self.pm.roots(ticketsByID):
            setEffectivePriority(pid, [])

    # Compare two tickets by their priority value.
    def compareTasks(self, t1, t2):
        return self.compareOneField('effectivePriority', t1, t2)

# ------------------------------------------------------------------------
# Handles dates, duration (estimate) dependencies, and resource
# leveling but not priorities when leveling resources.
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
# Differs from CalendarScheduler only in keeping track of when
# resources are available.
class ResourceScheduler(Component):
    implements(ITaskScheduler)

    pm = None
    calendar = None
    sorter = None

    # The ResourceScheduler uses the Bridge design pattern to separate
    # the overall scheduling process from the implementation of
    # prioritizing tasks, via an ITaskSorter implementation and
    # determining resource availability, via an IResourceCalendar
    # implementation.
    #
    # We identify all the enabled implementations via ExtensionPoint()
    # then use _mixIn() to pick one (if more than one is enabled).

    # Find any enabled sorters and calendars.  We'll pick one each in __init__
    sorters = ExtensionPoint(ITaskSorter)
    calendars = ExtensionPoint(IResourceCalendar)

    # Pick one of N enabled implementations of interface or fall back
    # to default if none are found.
    #   interface - The name of the interface (e.g., 'ITaskSorter')
    #   expt - The extension point to process
    #   default - default implementation to use
    def _mixIn(self, interface, extpt, default = None):
        # Count the enabled implementations
        i = 0
        for e in extpt:
            i += 1

        # If none
        if i == 0:
            # Use default, if set
            if default:
                self.env.log.info(('No %s implementations enabled. ' +
                                   'Using default, %s') % 
                                  (interface, default))
                e = default(self.env)
            # Otherwise, we can't go on.
            else:
                raise TracError('No %s implementations enabled.' % interface)
        # If more than one, log the one we picked.
        elif i > 1:
            self.env.log.info(('Found %s enabled %s implementations.  ' +
                              'Using %s.') % 
                              (i, interface, e))

        # Return the chosen (or default) implementation.
        return e

    def __init__(self):
        # Instantiate the PM component
        self.pm = TracPM(self.env)

        self.calendar = self._mixIn('IResourceCalendar',
                                    self.calendars,
                                    SimpleCalendar)

        self.sorter = self._mixIn('ITaskSorter',
                                  self.sorters,
                                  SimpleSorter)

        self.logEnabled = self.config.get('TracPM', 'logScheduling', '0')



    # Log scheduling progress.
    def _logSch(self, msg):
        if self.logEnabled == '1':
            self.env.log.info(msg)

    # ITaskScheduler method
    # Uses options hoursPerDay and schedule (alap or asap).
    def scheduleTasks(self, options, ticketsByID):
        # The earliest (latest) time a resource is available for the
        # next task in an ALAP (ASAP) schedule.  Indexed by
        # owner/user.  Elements are a datetime.
        #
        # Need to clear these every time we schedule.
        self.limits = {}
        self.taskStack = []

        # Return a time delta hours (positive or negative) from
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
                available = self.calendar.hoursAvailable(f, ticket['owner'])

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
                    if pid:
                        if pid in ticketsByID:
                            parent = ticketsByID[pid]
                            _schedule_task_alap(parent)
                            if _betterDate(ticketsByID[pid]['_calc_finish'],
                                           finish):
                                finish = ticketsByID[pid]['_calc_finish']
                        else:
                            self.env.log.info(('Ticket %s has parent %s ' +
                                               'but %s is not in the chart. ' +
                                               'Ancestor deadlines ignored.') %
                                              (t['id'], pid, pid))
                self._logSch('ancestor finish for %s is %s' %
                             (t['id'], finish))
                return copy.copy(finish)

            # Find the earliest start of any successor
            # t is a ticket (list of ticket fields)
            # start is a tuple ([date, explicit])
            def _earliest_successor(t, start):
                for tid in self.pm.successors(t):
                    if tid in ticketsByID:
                        s = _schedule_task_alap(ticketsByID[tid])
                        if _betterDate(s, start) and \
                                start == None or \
                                (s and start and s[0] < start[0]):
                            start = s
                    else:
                        self.env.log.info(('Ticket %s has successor %s ' +
                                           'but %s is not in the chart. ' +
                                           'Dependency deadlines ignored.') %
                                          (t['id'], tid, tid))
                self._logSch('earliest successor for %s is %s' %
                             (t['id'], start))
                return copy.copy(start)

            # If we found a loop, tell the user and give up.
            if t['id'] in self.taskStack:
                # We want to show the whole loop so add the current ID
                # to the list
                self.taskStack.append(t['id'])
                # Not much we can do at this point so show the user
                # the data error
                raise TracError('Ticket %s is part of a loop: %s' %
                                (t['id'], 
                                 '->'.join([str(t) for t in self.taskStack])))

            self.taskStack.append(t['id'])

            # If we haven't scheduled this yet, do it now.
            if t.get('_calc_finish') == None:
                # If this ticket is closed, the finish is the actual finish.
                if t.get('_actual_finish') and options.get('useActuals'):
                    finish = [ to_datetime(t['_actual_finish']), True ]
                # If there is a precomputed finish in the database,
                # use it unless we're forcing a schedule calculation.
                elif t.get('_sched_finish') and not options.get('force'):
                    finish = [ to_datetime(t['_sched_finish']), True ]
                # If there is a user-supplied finish (due date) set, use it
                elif self.pm.isSet(t, 'finish'):
                    # Don't adjust for work week; use the explicit date.
                    finish = self.pm.parseFinish(t)
                    finish += timedelta(hours=options['hoursPerDay'])
                    finish = [finish, True]
                # Otherwise, compute finish from dependencies.
                else:
                    finish = _earliest_successor(t, _ancestor_finish(t))

                    # The finish derived from the earliest successor
                    # is *not* a fixed (user-specified) date.
                    if finish != None:
                        finish[1] = False
                    # If dependencies don't give a date, use finish of
                    # project.  Default to today if none given.
                    else:
                        # Finish at user-supplied finish for schedule.
                        finish = self.pm.parseDbDate(options.get('finish'))
                        # If none, finish at midnight today
                        if finish == None:
                            finish = datetime.today().replace(hour=0, 
                                                              minute=0, 
                                                              second=0, 
                                                              microsecond=0,
                                                              tzinfo=localtz)
                        # Move ahead to beginning of next day so fixup
                        # below will handle work week.
                        finish += timedelta(days=1)

                        finish = [finish, False]
                        self._logSch('Defaulted finish for %s to %s' %
                                     (t['id'], finish))

                # Check resource availability.  Can't start later than
                # earliest available time.
                #
                # NOTE: Milestones don't require any work and closed
                # tickets don't require any (more) work so they don't
                # need to be resource leveled.
                if options.get('doResourceLeveling') == '1' and \
                        t['type'] != self.pm.goalTicketType and \
                        t['status'] != 'closed':
                    limit = self.limits.get(t['owner'])
                    if limit and limit < finish[0]:
                        finish = [limit, True]
                        # FIXME - This doesn't handle explicit finish
                        # dates.  End up with negative durations.

                # If we are to finish at the beginning of the work
                # day, our finish is really the end of the previous
                # work day
                if self.pm.isStartOfDay(finish[0]):
                    f = finish[0]
                    # Move back one hour from start of day to make
                    # sure finish is on a work day.
                    f += _calendarOffset(t, -1, f)
                    # Move forward one hour to the end of the day
                    f += timedelta(hours=1)
                    finish[0] = f
                    self._logSch('Adjusted finish of %s to end of day, %s' %
                                 (t['id'], finish))

                # Set the field
                t['_calc_finish'] = finish

            if t.get('_calc_start') == None:
                # If work has begun, the start is the actual start.
                if t.get('_actual_start') and options.get('useActuals'):
                    start = [ to_datetime(t['_actual_start']), True ]
                # If there is a precomputed start in the database,
                # use it unless we're forcing a schedule calculation.
                elif t.get('_sched_start') and not options.get('force'):
                    start = [ to_datetime(t['_sched_start']), True ]
                # If there is an explicit start date, use it.
                elif self.pm.isSet(t, 'start'):
                    start = self.pm.parseStart(t)
                    start = [start, True]
                # Otherwise, the start is based on the finish and the
                # work to be done before then.
                else:
                    hours = self.pm.workHours(t)
                    start = t['_calc_finish'][0] + \
                        _calendarOffset(t, 
                                        -1*hours, 
                                        t['_calc_finish'][0])
                    start = [start, t['_calc_finish'][1]]

                t['_calc_start'] = start

                # Adjust implicit finish for explicit start
                if _betterDate(start, finish):
                    hours = self.pm.workHours(t)
                    finish[0] = start[0] + _calendarOffset(t,
                                                           hours,
                                                           start[0])
                    t['_calc_finish'] = finish


            # Remember the limit for open tickets
            if t['status'] != 'closed':
                limit = self.limits.get(t['owner'])
                if not limit or limit > t['_calc_start'][0]:
                    self.limits[t['owner']] = t['_calc_start'][0]

            self.taskStack.pop()

            return t['_calc_start']

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
                    if pid:
                        if pid in ticketsByID:
                            parent = ticketsByID[pid]
                            _schedule_task_asap(parent)
                            if _betterDate(ticketsByID[pid]['_calc_start'], 
                                           start):
                                start = ticketsByID[pid]['_calc_start']
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
                for tid in self.pm.predecessors(t):
                    if tid in ticketsByID:
                        f = _schedule_task_asap(ticketsByID[tid])
                        if _betterDate(f, finish) and \
                                finish == None or \
                                (f and finish and f[0] > finish[0]):
                            finish = f
                    else:
                        self.env.log.info(('Ticket %s has predecessor %s ' +
                                           'but %s is not in the chart. ' +
                                           'Dependency deadlines ignored.') %
                                          (t['id'], tid, tid))
                return copy.copy(finish)

            # If we found a loop, tell the user and give up.
            if t['id'] in self.taskStack:
                # We want to show the whole loop so add the current ID
                # to the list
                self.taskStack.append(t['id'])
                # Not much we can do at this point so show the user
                # the data error
                raise TracError('Ticket %s is part of a loop: %s' %
                                (t['id'], 
                                 '->'.join([str(t) for t in self.taskStack])))

            self.taskStack.append(t['id'])

            # If we haven't scheduled this yet, do it now.
            if t.get('_calc_start') == None:
                # If work has begun, the start is the actual start.
                if t.get('_actual_start') and options.get('useActuals'):
                    start = [ to_datetime(t['_actual_start']), True ]
                # If there is a precomputed start in the database,
                # use it unless we're forcing a schedule calculation.
                elif t.get('_sched_start') and not options.get('force'):
                    start = [ to_datetime(t['_sched_start']), True ]
                # If there is a start set, use it
                elif self.pm.isSet(t, 'start'):
                    # Don't adjust for work week; use the explicit date.
                    start = self.pm.parseStart(t)
                    start = [start, True]
                # Otherwise, compute start from dependencies.
                else:
                    start = _latest_predecessor(t, _ancestor_start(t))

                    # The start derived from the latest predecessor is
                    # *not* a fixed (user-specified) date.
                    if start != None:
                        start[1] = False
                    # If dependencies don't give a date, use start of
                    # project.  Default to today if none given.
                    else:
                        # Start at user-supplied start for schedule.
                        start = self.pm.parseDbDate(options.get('start'))
                        # If none, start at midnight today
                        if start == None:
                            start = datetime.today().replace(hour=0, 
                                                             minute=0, 
                                                             second=0, 
                                                             microsecond=0,
                                                             tzinfo=localtz)

                        # Move back to end of previous day so fixup
                        # below will handle work week.
                        start += timedelta(days=-1,
                                           hours=options['hoursPerDay'])
                        start = [start, False]

                # Check resource availability.  Can't finish earlier than
                # latest available time.
                #
                # NOTE: Milestones don't require any work and closed
                # tickets don't require any (more) work so they don't
                # need to be resource leveled.
                if options.get('doResourceLeveling') == '1' and \
                        t['type'] != self.pm.goalTicketType and \
                        t['status'] != 'closed':
                    limit = self.limits.get(t['owner'])
                    if limit and limit > start[0]:
                        start = [limit, True]

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
                t['_calc_start'] = start

            if t.get('_calc_finish') == None:
                # If this ticket is closed, the finish is the actual finish.
                if t.get('_actual_finish') and options.get('useActuals'):
                    finish = [ to_datetime(t['_actual_finish']), True ]
                # If there is a precomputed finish in the database,
                # use it unless we're forcing a schedule calculation.
                elif t.get('_sched_finish') and not options.get('force'):
                    finish = [ to_datetime(t['_sched_finish']), True ]
                elif self.pm.isSet(t, 'finish'):
                    # Don't adjust for work week; use the explicit date.
                    finish = self.pm.parseFinish(t)
                    finish += timedelta(hours=options['hoursPerDay'])
                    finish = [finish, True]
                # Otherwise, the start is based on the finish and the
                # work to be done before then.
                else:
                    hours = self.pm.workHours(t)
                    finish = t['_calc_start'][0] + \
                        _calendarOffset(t,
                                        +1*hours,
                                        t['_calc_start'][0])
                    finish = [finish, start[1]]

                t['_calc_finish'] = finish

                # Adjust implicit start for explicit finish
                if _betterDate(finish, start):
                    hours = self.pm.workHours(t)
                    start[0] = finish[0] + _calendarOffset(t, 
                                                           -1*hours, 
                                                           finish[0])
                    t['_calc_start'] = start

            # Remember the limit for open tickets
            if t['status'] != 'closed':
                limit = self.limits.get(t['owner'])
                if not limit or limit < t['_calc_finish'][0]:
                    self.limits[t['owner']] = t['_calc_finish'][0]

            self.taskStack.pop()

            return t['_calc_finish']

        # Augment tickets in a scheduler-specific way to make
        # scheduling easier 
        #
        # If a parent task has a dependency, copy it to its children.
        def _augmentTickets(ticketsByID):

            # Propagate dependencies.
            self.pm.augmentTickets(ticketsByID)

            # For each ticket to schedule
            for tid in ticketsByID:
                ticket = ticketsByID[tid]

                # Count predecessors and successors in tickets being
                # scheduled.
                if self.pm.isCfg('pred'):
                    pred = self.pm.predecessors(ticket)
                    pred = [p for p in pred if p in ticketsByID]
                    ticket['npred'] = len(pred)
                else:
                    ticket['npred'] = 0

                if self.pm.isCfg('succ'):
                    succ = self.pm.successors(ticket)
                    succ = [s for s in succ if s in ticketsByID]
                    ticket['nsucc'] = len(succ)
                else:
                    ticket['nsucc'] = 0

        # This function implements a simple serial-SGS (Solution
        # Generation Scheme) as suggested by Briand and Bezanger in
        # "An any-order SGS for project scheduling with scarce
        # resources and precedence constraints":
        # 
        #   A serial-SGS consists of n interations: In each iteration,
        #   an activity is selected according to its priority and
        #   inserted inside a partial schedule at the earliest
        #   ... Only an eligible activity can be selected at each
        #   iteration.  An activity is eligible if all its
        #   predecessors have already been scheduled.  The priorities
        #   are determined according to [a] rule [outside the SGS].
        #
        # Our ASAP schedule follows their description.  ALAP reverses
        # it (scheduling the last task, then any task with all of its
        # successors already scheduled, etc.
        #
        # One difference from their algorithm description is they step
        # through time, chosing tasks that might be done then.  We
        # step through tasks and let time fall where it may.
        #
        #  scheduleFunction - schedule one task
        #  eligibleField - when ticket[eligibleField] is 0, the ticket
        #      is eligible
        #  nextIndex - index of best ticket in elibigle list
        #  dependentFunction - Get list of dependents to update
        #      eligibleField in
        def serialSGS(scheduleFunction,
                      eligibleField, 
                      nextIndex, 
                      dependentFunction):
            unscheduled = ticketsByID.keys()

            # FIXME - Sometimes, eligible includes a group which has
            # children which have predecessors or successors.  Do I
            # need to propagate dependencies up, too?  This seems to
            # work but I guess needs more testing.
            eligible = [ticketsByID[tid] for tid in unscheduled \
                            if ticketsByID[tid][eligibleField] == 0]

            details = False
            while unscheduled and eligible:
                # FIXME - Maybe sort after adding some. I may not need
                # to sort every loop.)
                eligible.sort(self.sorter.compareTasks)
                if details:
                    self.env.log.debug('Eligible tickets:%s' %
                                       [t['id'] for t in eligible])
                # Schedule the best eligible task
                ticket = eligible.pop(nextIndex)
                tid = ticket['id']
                if tid in unscheduled:
                    unscheduled.remove(tid)
                    if details:
                        self.env.log.debug('  scheduling:%s' % tid)
                        self.env.log.debug('  unscheduled:%s' % unscheduled)
                else:
                    self.env.log.debug('Could not remove %s from unscheduled list' % tid)
                    self.env.log.debug(' unscheduled:%s' % unscheduled)
                    self.env.log.debug(' ticket:%s' % ticket)
                    self.env.log.debug(' eligible:%s' % eligible)
                    raise TracError('Could not remove %s from unscheduled list' % tid)

                scheduleFunction(ticket)

                # Decrement number of unscheduled successors for each
                # predecessor (or vice versa).  Any ticket that ends
                # up with no unscheduled dependents is now eligible to
                # schedule.
                for tid in dependentFunction(ticket):
                    if tid in ticketsByID:
                        other = ticketsByID[tid]
                        other[eligibleField] -= 1
                        if other[eligibleField] == 0:
                            eligible.append(other)

                if not eligible and len(unscheduled):
                    details = True
                    self.env.log.error('Not all tickets scheduled')
                    self.env.log.error('%s remain ineligible.  Scheduling.' %
                                       unscheduled)
                    eligible = [ticketsByID[tid] for tid in unscheduled]
                    # Make sure we don't add them again
                    for ticket in eligible:
                        ticket[eligibleField] = 0

        # Main schedule processing

        # Add data to tickets to facilitate scheduling.Propagate
        _augmentTickets(ticketsByID)

        # Make sure sorting (compareTasks, below) works.
        self.sorter.prepareTasks(ticketsByID)

        # If schedule option is present and 'asap', do that.
        # Otherwise, fall through to default to ALAP.
        if options.get('schedule') == 'asap':
            # Schedule ASAP.
            # Eligible tasks are those with npred==0.
            # The best eligible task is first (0) after sorting.
            # Update successors after scheduling a task
            serialSGS(_schedule_task_asap, 'npred', 0, self.pm.successors)
        elif options.get('schedule') == 'alap':
            # Schedule ALAP.
            # Eligible tasks are those with nsucc==0.
            # The best eligible task is last (-1) after sorting.
            # Update predecessors after scheduling a task
            serialSGS(_schedule_task_alap, 'nsucc', -1, self.pm.predecessors)
        else:
            # Don't schedule.  But some milestones may not have due dates.
            # Set them from the latest ticket in the milestone.

            # Get IDs of milestone pseudotickets.
            milestoneIDs = [tid for tid in ticketsByID.keys() \
                              if self.pm.isTracMilestone(ticketsByID[tid]) \
                                and not self.pm.finish(ticketsByID[tid])]

            # Get IDs of all other tickets.
            ticketIDs = [tid for tid in ticketsByID.keys() \
                             if tid not in milestoneIDs]

            # Process each milestone, setting the start and finish
            # from the latest ticket in the milestone.
            for mid in milestoneIDs:
                ms = ticketsByID[mid]
                # Find the latest ticket in the milestone
                msDue = None
                for tid in ticketIDs:
                    t = ticketsByID[tid]
                    if t['milestone'] == ms['milestone'] \
                            and (not msDue or msDue < self.pm.finish(t)):
                        msDue = self.pm.finish(t)

                # A milestone has no duration (start == finish)
                ms['_calc_start'] = [msDue, True]
                ms['_calc_finish'] = [msDue, True]

# FIXME - need to react to milestone changes, too (for dates).  0.11.6
# doesn't have a milestone change listener.  I belive a later version
# does.
class TicketRescheduler(Component):
    implements(ITicketChangeListener)

    pm = None
    scheduleFields = None
    options = {}

    def __init__(self):
        self.pm = TracPM(self.env)

        self.scheduleFields = []

        # Built-in fields that can affect scheduling
        self.scheduleFields = ['owner', 'priority', 'milestone']

        # Configurable fields from plugins that can affect scheduling
        for f in ['estimate', 'start', 'finish', 'pred', 'succ', 'parent']:
            # If the user configured this field
            if f in self.pm.fields:
                # Get the name of the configured field
                self.scheduleFields.append(self.pm.fields[f])

        # FIXME - Make this configurable
        self.scheduleFields.append('parents')
        self.scheduleFields.append('blocking')
        self.scheduleFields.append('blockedby')

        self.options['schedule'] = \
            self.config.get('TracPM', 'option.schedule', 'asap')
        self.options['hoursPerDay'] = \
            float(self.config.get('TracPM', 'option.hoursPerDay', '6.0'))
        self.options['doResourceLeveling'] = \
            self.config.get('TracPM', 'option.doResourceLeveling', '1')

        # When recomputing the schedule, we have to ignore the
        # database and compute all start/finish times so we can then
        # compare to the database and store changes.
        self.options['force'] = True

    # Do any of the fields that changed affect scheduling?  For
    # example, component would not but owner, and dependencies would.
    # Some of the ones that affect scheduling are built-in (e.g.,
    # owner) some are not (e.g., blockedby).
    #
    # @param ticket ticket object as passed to ticket change listener
    # @param old_values old ticket values as passed to change listener
    #
    # @return True if changes in old_values affect schedule
    # 
    # FIXME - Should this be in the TracPM class?
    def _affectsSchedule(self, ticket, old_values):
        # If any of the changed values are schedule related
        for f in old_values:
            if f in self.scheduleFields:
                return True

        # If the status changed, check for closing or reopening
        # tickets and making goals active or inactive.
        if 'status' in old_values:
            # If the ticket changed status in or out of closed, reschedule
            if (old_values['status'] == 'closed' \
                    or ticket['status'] == 'closed'):
                return True

            # If the ticket is a goal and changes status in or out of
            # active, reschedule
            if ticket['type'] == self.pm.goalTicketType:
                wasActive = old_values['status'] in self.pm.activeGoalStatuses
                isActive = ticket['status'] in self.pm.activeGoalStatuses
                if (wasActive and not isActive) \
                        or (isActive and not wasActive):
                    return True

        return False

    # Find tickets related to this one (before and after changes).
    #
    # Find IDs of all tickets affected by changing this ticket's
    # schedule:
    #  Same owner
    #  Any successors, predecessors
    #  Any ancestors, descendants
    # @param ticket ticket object passed to change listener
    # @param old_values list of old values passed to change listener
    #
    # @return a list of ticket ID strings
    def _findAffected(self, ticket, old_values):
        # Helper to find owners of tickets
        # @param ids set of tickets ID strings
        # @return set of owner strings
        def ownersOf(ids):
            db = self.env.get_db_cnx()
            inClause = "IN (%s)" % ','.join(('%s',) * len(ids))
            cursor = db.cursor()
            cursor.execute(("SELECT DISTINCT owner FROM ticket "
                            "WHERE id " + 
                           inClause),
                           list(ids))
            owners = [row[0] for row in cursor]
            return set(owners)

        # Helper to find open tickets by owners
        # @param owners set of owner strings from tickets
        # @return a set of ticket ID strings for tickets owned by owners
        def openByOwner(owners):
            # FIXME - this may fix a bug I don't have any more.
            if len(owners) == 0:
                return set()
            db = self.env.get_db_cnx()
            inClause = "IN (%s)" % ','.join(('%s',) * len(owners))
            cursor = db.cursor()
            cursor.execute(("SELECT id FROM ticket "
                            "WHERE status!=%s AND owner " + 
                           inClause),
                           ['closed'] + list(owners))
            ids = ['%s' % row[0] for row in cursor]
            return set(ids)


        # Find all the tickets affected by the old values.  For
        # example if processing ticket A which used to be a
        # prerequisite for B but isn't any longer, B will be in
        # old_values['blocking'] and may be able to start earlier now.
        #
        # @param old_values as passed to TicketChangeListener
        #
        # @return set of ticket ID strings
        #
        # FIXME - need better tests here; this assumes Master Tickets
        # and Subtickets plugins.
        def affectedByOld(old_values):
            affected = set()

            if 'parents' in old_values.keys() \
                    and len(old_values['parents']) != 0:
                affected.add(str(old_values['parents']))
            if 'blockedby' in old_values.keys() \
                    and len(old_values['blockedby']) != 0:
                affected |= \
                    set([x.strip() 
                         for x in old_values['blockedby'].split(',')])
            if 'blocking' in old_values.keys() \
                    and len(old_values['blocking']) != 0:
                affected |= \
                    set([x.strip() 
                         for x in old_values['blocking'].split(',')])

            # If owner changed, get tickets by old owner.  (New owner is
            # handled by more())
            if 'owner' in old_values.keys():
                owners = set()
                owners.add(old_values['owner'])
                affected |= openByOwner(owners)

            return affected


        # Used by more(), below, to optimize queries. (I'd like a
        # better scope but Python doesn't do closures the way I
        # expected.)
        self.knownOwners = set()

        # Helper to expand set of tickets by one generation
        #
        # FIXME - passing 1 as depth to _reachable() misses some
        # closed but reachable tickets.  In my test data, I don't get
        # 150, a child of 149.  Other children of 149 show up.
        #
        # @param ids set of ticket ID strings to find more tickets from
        # @return set of IDs for tickets related to ids
        def more(ids):
            n = set(self.pm._reachable(list(ids)))

            # Get owners for these tickets
            newOwners = ownersOf(n)

            # Remove owners we already know
            newOwners -= self.knownOwners

            # If we don't already have all these owners, process the new ones
            if len(newOwners) != 0:
                # Add new owners to known owners
                self.knownOwners |= newOwners

                # Get tickets for the new owners
                x = openByOwner(newOwners)

                # Remove known tickets
                x -= ids

                # Add new tickets to set
                n |= x

            return n

        # The set of tickets that may be affected by this change.
        affected = set()
        # The changed ticket is affected
        affected.add(str(ticket.id))

        # Tickets referenced in old values
        affected |= affectedByOld(old_values)

        # Find all tickets reachable from the list we've built so far
        #
        # NOTE: The last loop finds all the tickets in explored that
        # are adjacent to the border and pruning gives an empty set.
        # You'd think I could stop one iteration earlier but I don't
        # know how.
        explored = set()
        toExplore = affected
        # FIXME - elsewhere I use "toExplore != set()".  Which is more
        # efficient?  Or clearer?
        while len(toExplore) != 0:
            border = toExplore
            toExplore = more(border)
            toExplore -= explored
            explored |= border

        return list(explored)

    # Remove tickets that are not required for any goal with one of
    # the configured active statuses.
    #
    #  1. mark all tickets inactive 
    #  2. for each active goal
    #    2.1 follow predecessor links to mark tickets active 
    #  3. Delete all inactive tickets (and fix up dependencies)
    # 
    # @param tickets a list of tickets
    #
    # @return the list with inactive tickets removed
    def _pruneInactive(self, tickets):
        # If no configured active statuses, don't prune.
        if not self.pm.activeGoalStatuses:
            return tickets

        # Make a lookup for faster processing
        ticketsByID = {}
        for t in tickets:
            ticketsByID[t['id']] = t

        # Copy dependencies from parents to children
        self.pm.augmentTickets(ticketsByID)

        # Mark all tickets inactive.
        for t in tickets:
            t['_active'] = False

        # Helper to traverse dependencies recursively
        def markActive(ticket):
            # If this ticket hasn't been processed yet
            if not ticket['_active']:
                # Mark it active
                ticket['_active'] = True
                # And propagate to predecessors
                for pid in self.pm.predecessors(ticket):
                    markActive(ticketsByID[pid])

        # All predecessors of active goals are active
        for t in tickets:
            # FIXME - encapsulate this test in "self.pm.activeGoal()"?
            if t['type'] == self.pm.goalTicketType \
                    and t['status'] in self.pm.activeGoalStatuses:
                markActive(t)

        # Remove inactive tickets
        tickets = [t for t in tickets if t['_active']]
        # Refresh the lookup table
        ticketsByID = {}
        for t in tickets:
            ticketsByID[t['id']] = t


        # Fairly often tickets is empty after pruning but setting up
        # the link field names is cheap and traversing an empty list
        # is basically free.

        # Clean up links to removed tickets
        #
        # FIXME - this is a really gross and fragile way to do it but
        # it'll due for now.
        linkFieldNames = {}
        for linkField in ['parent', 'pred', 'succ']:
            if not self.pm.isCfg(linkField):
                linkFieldNames[linkField] = None
            elif self.pm.isField(linkField):
                linkFieldNames[linkField] = \
                    self.pm.fields[self.pm.sources[linkField]]
            else:
                linkFieldNames[linkField] = linkField

        for t in tickets:
            # Remove link to parent
            pid = self.pm.parent(t)
            if pid and pid not in ticketsByID:
                t[linkFieldNames['parent']] = None

            # Remove links to children
            # (Include only children still in the set)
            t['children'] = [cid for cid in t['children'] 
                             if cid in ticketsByID]

            # Predecessors and successors
            for linkField in ['pred', 'succ']:
                if linkFieldNames[linkField]:
                    t[linkFieldNames[linkField]] = \
                        [tid for tid in t[linkFieldNames[linkField]]
                         if tid in ticketsByID]

        return tickets


    # Query ticket table (and linked custom fields) for fields needed
    # to reschedule
    #
    # @param ids list of ticket IDs to get data for
    #
    # @return list of hashes for tickets
    def queryTickets(self, ids):
        options = {}
        options['max'] = 0
        options['id'] = "|".join(ids)

        return self.pm.query(options, set())

    ##
    # Update in-memory relationships because other plugins' ticket
    # change listeners may not have run yet so the database may be
    # stale.
    #
    # @param tickets list of tickets to examine
    # @param ticket ticket that changed
    # @param old_values previous values for fields in ticket which changed
    #
    # Note: ticket and old_values are passed to ITicketChangeListener
    # methods.
    # 
    # FIXME - this is very specific to Subtickets and MasterTickets
    # and accesses fields directly instead of using accessor
    # functions.  Let's make it work *then* make it pretty.
    #
    # MasterTickets and Subtickets both maintain relationships in
    # private tables but maintain custom fields which summarize or
    # preview the relationships when viewing tickets.  Most of TracPM
    # abstracts access to the private tables but since this is called
    # from a ticket change listener, we have only the custom fields to
    # work with.
    def spliceGraph(self, tickets, ticket, old_values):
        # See if any of the changed values are for custom relationship
        # fields.
        relationshipChanged = False
        for f in old_values:
            # FIXME - these are the custom field names for Subtickets
            # and MasterTickets.  Should be configurable or flexible
            # somehow.
            if f in [ 'parents', 'blockedby', 'blocking' ]:
                relationshipChanged = True

        # If a relationship changed, process it.
        if relationshipChanged:
            # Relationships can be configured to be access via fields
            # or via a relation.  This bit -- copied from
            # _pruneInactive -- builds a lookup encapsulating that
            # configuration and simplifying the update logic which
            # follows.
            #
            # 'parent', 'pred', and 'succ' are the names of the
            # relationships.  This code determines which field holds
            # the data for that relationship.
            linkFieldNames = {}
            for linkField in [ 'parent', 'pred', 'succ']:
                if not self.pm.isCfg(linkField):
                    linkFieldNames[linkField] = None
                elif self.pm.isField(linkField):
                    linkFieldNames[linkField] = \
                        self.pm.fields[self.pm.sources[linkField]]
                else:
                    linkFieldNames[linkField] = linkField

            # Table indexed by ticket ID for faster updates
            ticketsByID = {}
            for t in tickets:
                ticketsByID[t['id']] = t


            # Fix up parent
            #
            # Note: the 'children' field is *always* internal to
            # TracPM.  It does not correspond to a custom field; no
            # known plugin for parent/child relationships has a custom
            # field for children.
            if linkFieldNames['parent'] in old_values:
                # Remove ticket from children of old parent
                parent = ticketsByID[old_values[[linkFieldsName['parent']]]]
                parent['children'] = \
                    [cid for cid in parent['children'] if cid != ticket.id]
                # Add ticket to children of new parent
                parent = ticketsByID[ticket[linkFieldsNames['parent']]]
                if ticket.id not in parent['children']:
                    parent['children'].append(ticket.id)

            # The custom fields which allow previewing predecessors
            # and successors.
            #
            # FIXME - these are the custom field names for
            # MasterTickets.  Should be configurable or flexible
            # somehow.
            previewFields = {}
            previewFields['pred'] = 'blockedby'
            previewFields['succ'] = 'blocking'

            # Fix up predecessors, successors
            for linkField in ['pred', 'succ']:
                # We need to figure up the forward and reverse
                # relationships below.
                fwd = linkField
                if fwd == 'pred':
                    rev = 'succ'
                else:
                    rev = 'pred'

                fwdField = linkFieldNames[fwd]
                revField = linkFieldNames[rev]

                # If the custom field summarizing this relationship
                # changed, we need to splice the graph.
                #
                # This code depends on the structure of the
                # relationship data in the graph (which TracPM
                # controls) and *not* on the name of any fields so it
                # should be correct regardless of what plugins are
                # being used.
                if previewFields[fwd] in old_values:
                    # Get the set of old and new dependants
                    if len(old_values[previewFields[fwd]]) == 0:
                        oldDependants = set()
                    else:
                        ids = old_values[previewFields[fwd]].split(',')
                        oldDependants = set([int(tid) for tid in ids])

                    if len(ticket[previewFields[fwd]]) == 0:
                        newDependants = set()
                    else:
                        ids = ticket[previewFields[fwd]].split(',')
                        newDependants = set([int(tid) for tid in ids])

                    # Set difference tells us what is in old and not
                    # new and vice versa.
                    removed = oldDependants - newDependants
                    added = newDependants - oldDependants

                    # Remove from both ends, if needed
                    for tid in removed:
                        ticketsByID[ticket.id][fwdField] = \
                            [did for did in 
                             ticketsByID[ticket.id][fwdField]
                             if did != tid]
                        ticketsByID[tid][revField] = \
                            [did for did in 
                             ticketsByID[tid][revField]
                             if did != ticket.id]

                    # Link on both ends, if needed
                    for tid in added:
                        if tid not in ticketsByID[ticket.id][fwdField]:
                            ticketsByID[ticket.id][fwdField].append(tid)
                            ticketsByID[tid][revField].append(ticket.id)


    # Reschedule based on a ticket changing.  
    #
    # Arguments as for TicketChangeListener.
    #
    # No return.  The calculated start and finish dates in the ticket
    # database may be updated.
    def rescheduleTickets(self, ticket, old_values):
        # All the history records need the same timestamp.
        dbTime = datetime.now().replace(tzinfo=localtz)

        # Each step (e.g., finding, querying, pruning) has an entry
        # Each entry is [ step, ticketcount, time ]
        profile = []

        # If this ticket is a goal and it is going inactive, the
        # tickets required for it will be idle unless they are
        # required for another still-active goal.
        potentiallyIdle = set()
        if self.pm.activeGoalStatuses \
                and ticket['type'] == self.pm.goalTicketType \
                and 'status' in old_values:
            wasActive = old_values['status'] in self.pm.activeGoalStatuses
            isActive = ticket['status'] in self.pm.activeGoalStatuses
            if wasActive and not isActive:
                start = datetime.now()
                potentiallyIdle |= self.pm.preQuery({'goal': str(ticket.id)})
                # All the rest of the ticket sets in this function are
                # the result of direct queries and have integer ticket
                # IDs.  preQuery() returns a set of strings so we
                # convert here to make later processing clearer.
                potentiallyIdle = set([int(t) for t in potentiallyIdle])
                # pretty_timedelta is ugly. :-/  Doesn't show fractional seconds
                end = datetime.now()
                profile.append([ 'remembering', 
                                 len(potentiallyIdle), 
                                 end - start ])

        # This ticket may go idle if it moves to another goal.
        potentiallyIdle.add(ticket.id)

        # What tickets are affected by this ticket changing?
        start = datetime.now()
        # Here ids is a list of strings.  Necessary for queryTickets()
        ids = self._findAffected(ticket, old_values)
        end = datetime.now()
        profile.append(['finding', len(ids), end - start ])

        # Get Details for the affected tickets.
        #
        # Note that the schedule information *is* stale.  Trac updated
        # 'ticket' and 'ticket_custom' but the code which follows
        # updates 'schedule' so it is still in the old state.
        #
        # Also, dependency information in 'mastertickets' *may* (or
        # may not) be stale depending on what order that plugin's
        # ticket change listener and this one are invoked in (which is
        # indeterminate and uncontrollable).
        start = datetime.now()
        tickets = self.queryTickets(ids)
        end = datetime.now()
        profile.append(['querying', len(tickets), end - start ])

        # Splice in-memory graph based on changes
        start = datetime.now()
        self.spliceGraph(tickets, ticket, old_values)
        end = datetime.now()
        profile.append([ 'splicing', len(tickets), end - start ])

        # Prune tickets to only those in active projects.
        start = datetime.now()
        activeIDs = [t['id'] for t in self._pruneInactive(tickets)]
        end = datetime.now()
        profile.append([ 'pruning', len(activeIDs), end - start ])

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # The newly-idle tickets are the ones that might have been
        # idled by the goal status transition and are not still
        # active.
        idle = potentiallyIdle - set(activeIDs)
        if len(idle) != 0:
            start = datetime.now()
            # Remove idle tickets from schedule
            inClause = "IN (%s)" % ','.join(('%s',) * len(idle))
            cursor.execute("DELETE FROM schedule WHERE ticket " + \
                               inClause,
                           list(idle))

            # And note idling in schedule history
            valuesClause = ','.join(('(%s,%s,%s,%s)',) * len(idle))
            values = []
            for t in tickets:
                if t['id'] in idle:
                    values.append(t['id'])
                    values.append(to_utimestamp(dbTime))
                    values.append(to_utimestamp(self.pm.start(t)))
                    values.append(to_utimestamp(self.pm.finish(t)))

            # New start and finish are null
            cursor.execute('INSERT INTO schedule_change' + \
                               ' (ticket, time,' + \
                               ' oldstart, oldfinish)' + \
                               ' VALUES %s' % valuesClause,
                           values)
            end = datetime.now()
            profile.append([ 'idling', len(idle), end - start ])


        # Reschedule only if there are tickets left after pruning and
        # that list includes the changed ticket.
        if len(activeIDs) > 0 and ticket.id in activeIDs:
            # Limit to the active tickets.
            tickets = [t for t in tickets if t['id'] in activeIDs]

            # Compute schedule with configured options 
            schedule = timedelta()
            self.env.log.info('Recomputing schedule with options:%s' % 
                              self.options)
            start = datetime.now()
            self.pm.recomputeSchedule(self.options, tickets)
            end = datetime.now()
            profile.append(['rescheduling', len(tickets), end - start ])

            # Reduce list to only those tickets that were rescheduled.
            tickets = [t for t in tickets if t.get('_rescheduled')]
            self.env.log.info('%s tickets rescheduled' % len(tickets))

            # Remove milestone pseudo-tickets because we don't save
            # their data.  The "id" of those tickets is not guaranteed
            # to be the same between two runs so the key to the
            # schedule tables would be meaningless.
            tickets = [t for t in tickets if not self.pm.isTracMilestone(t)]

            # Update the database for any rescheduled tickets
            if len(tickets) != 0:
                ids = [t['id'] for t in tickets]

                # Some "rescheduled" tickets had their schedule created
                # for the first time, some had it changed.  We have to be
                # able to choose between UPDATE (for those that changed)
                # and INSERT (for the others).
                #
                # First, find which are already there.
                # (Query and save old start, finish values at the same time.)
                inClause = "IN (%s)" % ','.join(('%s',) * len(ids))
                cursor.execute("SELECT ticket, start, finish" + \
                                   " FROM schedule WHERE ticket " + \
                                   inClause,
                               ids)
                toUpdate = set()
                historyValues = {}
                for row in cursor:
                    tid = row[0]
                    oldStart = row[1]
                    oldFinish = row[2]

                    historyValues[tid] = [ oldStart, oldFinish ]

                    toUpdate.add(tid)


                # Second, update the tickets that are there.
                # (Build before/after values as we go to update history next.)
                start = datetime.now()
                values = []
                for t in tickets:
                    if t['id'] in toUpdate:
                        # Index history by ticket ID and time
                        values.append(t['id'])
                        values.append(to_utimestamp(dbTime))
                        # Old start and finish
                        values.append(historyValues[t['id']][0])
                        values.append(historyValues[t['id']][1])
                        # New start and finish
                        values.append(to_utimestamp(self.pm.start(t)))
                        values.append(to_utimestamp(self.pm.finish(t)))

                        cursor.execute('UPDATE schedule'
                                       ' SET start=%s, finish=%s'
                                       ' WHERE ticket=%s',
                                       (to_utimestamp(self.pm.start(t)),
                                        to_utimestamp(self.pm.finish(t)),
                                        t['id']))


                # Third, insert the history for the updated tickets.
                if len(toUpdate) != 0:
                    valuesClause = ','.join(('(%s,%s,%s,%s,%s,%s)',) 
                                            * len(toUpdate))
                    cursor.execute('INSERT INTO schedule_change' + \
                                       ' (ticket, time,' + \
                                       ' oldstart, oldfinish,' + \
                                       ' newstart, newfinish)' + \
                                       ' VALUES %s' % valuesClause,
                                   values)

                end = datetime.now()
                profile.append([ 'updating', len(toUpdate), end - start ])


                # Fourth, insert tickets that aren't already in the schedule
                toInsert = set(ids) - toUpdate
                start = datetime.now()
                if len(toInsert) != 0:
                    valuesClause = ','.join(('(%s,%s,%s)',) * len(toInsert))
                    values = []
                    for t in tickets:
                        if t['id'] in toInsert:
                            values.append(t['id']) 
                            values.append(to_utimestamp(self.pm.start(t)))
                            values.append(to_utimestamp(self.pm.finish(t)))
                    cursor.execute('INSERT INTO schedule' + \
                                       ' (ticket, start, finish)' + \
                                       ' VALUES %s' % valuesClause,
                                   values)


                    # Finally, add history records to schedule_change
                    # for newly scheduled tickets.
                    valuesClause = ','.join(('(%s,%s,%s,%s)',) * len(toInsert))
                    values = []
                    for t in tickets:
                        if t['id'] in toInsert:
                            values.append(t['id'])
                            values.append(to_utimestamp(dbTime))
                            # Old start and finish are null
                            values.append(to_utimestamp(self.pm.start(t)))
                            values.append(to_utimestamp(self.pm.finish(t)))
                    cursor.execute('INSERT INTO schedule_change' + \
                                       ' (ticket, time,' + \
                                       ' newstart, newfinish)' + \
                                       ' VALUES %s' % valuesClause,
                                   values)

                end = datetime.now()
                profile.append([ 'inserting', len(toInsert), end - start ])

        for step in profile:
            self.env.log.info('%s %s tickets took %s' % 
                              (step[0], step[1], step[2]))

    # ITicketChangeListener methods
    #
    # The change listener methods get called after all changes have
    # been saved to the database.

    def ticket_created(self, ticket):
        self.rescheduleTickets(ticket, {})


    def ticket_changed(self, ticket, comment, author, old_values):
        if self._affectsSchedule(ticket, old_values):
            self.env.log.info('Changes to %s affect schedule.  Rescheduling.' %
                              ticket.id)
            self.rescheduleTickets(ticket, old_values)


    def ticket_deleted(self, ticket):
        self.rescheduleTickets(ticket, {})
