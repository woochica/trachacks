import re
import time
import datetime
from datetime import timedelta, date
from operator import itemgetter, attrgetter

from trac.util.datefmt import format_date
from trac.util.html import Markup
from trac.wiki.macros import WikiMacroBase
from trac.web.chrome import Chrome
import copy
from trac.ticket.query import Query

from trac.core import implements, Component
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from pkg_resources import resource_filename

from trac.wiki.api import parse_args


class TracJSGanttSupport(Component):
    implements(IRequestFilter, ITemplateProvider)

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
    def __init__(self):
        # All the macro's options with default values.
        # Anything else passed to the macro is a TracQuery field.
        self.options = {
            'format': 'day',
            'sample': 0,
            'res': 1,
            'dur': 1,
            'comp': 1,
            'caption': 'Resource',
            'startDate': 1,
            'endDate': 1,
            'dateDisplay': 'mm/dd/yyyy',
            'openLevel': 999,
            'colorBy' : 'priority',
            'lwidth' : None,
            'root' : None,
            'showdep' : 1,
            }

        # self.options defaults are configurable from trac.ini
        for opt in self.options.keys():
            v = self.config.get('trac-jsgantt','option.%s' % opt, default=self)
            if v != self:
                if isinstance(self.options[opt], (int, long)):
                    v = int(v)
                self.options[opt] = v

        # Configuration fields
        self.fields = {}
        self.fields['percent'] = \
            self.config.get('trac-jsgantt','fields.percent', default=None)
        self.fields['estimate'] = \
            self.config.get('trac-jsgantt','fields.estimate', default=None)
        self.fields['worked'] = \
            self.config.get('trac-jsgantt','fields.worked', default=None)
        self.fields['start'] = \
            self.config.get('trac-jsgantt','fields.start', default=None)
        self.fields['finish'] = \
            self.config.get('trac-jsgantt','fields.finish', default=None)
        self.fields['pred'] = \
            self.config.get('trac-jsgantt','fields.pred', default=None)
        self.fields['succ'] = \
            self.config.get('trac-jsgantt','fields.succ', default=None)
        self.fields['parent'] = \
            self.config.get('trac-jsgantt','fields.parent', default=None)

        # This is the format of start and finish in the Trac database
        self.dbDateFormat = \
            str(self.config.get('trac-jsgantt',
                                'date_format', 
                                default='%Y-%m-%d'))

        # These have to be in sync.  jsDateFormat is the date format
        # that the JavaScript expects dates in.  It can be one of
        # 'mm/dd/yyyy', 'dd/mm/yyyy', or 'yyyy-mm-dd'.  pyDateFormat
        # is a strptime() format that matches jsDateFormat.  As long
        # as they are in sync, there's no real reason to change them.
        self.jsDateFormat = 'yyyy-mm-dd'
        self.pyDateFormat = '%Y-%m-%d'

        # Tickets of this type will be displayed as milestones.
        self.milestoneType = self.config.get('trac-jsgantt',
                                             'milestone_type', 
                                             default='milestone')

        # Days per estimate unit.  
        #
        # If estimate is in hours, and a day is 8 hours, this would be
        # 1/8 or 0.125.  If you assume only 6 productive hours per day
        # this is 1/6 or 0.1666.
        # 
        # float('1/6') is an error so the value must be a number, not
        # an equation.
        self.dpe = float(self.config.get('trac-jsgantt',
                                         'days_per_estimate', 
                                         default='0.125'))

        # User name map
        self.user_map = {}
        for username, name, email in self.env.get_known_users():
            self.user_map[username] = name

	# Parent format option
	self.parent_format = \
		self.config.get('trac-jsgantt','parent_format', default='%s')

    def _begin_gantt(self, options):
        format = options['format']
        showdep = options['showdep']
        text = ''
        text += '<div style="position:relative" class="gantt" id="GanttChartDIV"></div>\n'
        text += '<script language="javascript">\n'
        text += 'var g = new JSGantt.GanttChart("g",document.getElementById("GanttChartDIV"), "%s", "%d");\n' % (format, showdep)
        text += 'var t;\n'
        text += 'window.addEventListener("resize", function () { g.Draw();\n }, false);'
        return text

    def _end_gantt(self, options):
        chart = ''
        chart += 'g.Draw();\n' 
        if options['showdep']:
            chart += 'g.DrawDependencies();\n'
        chart += '</script>\n'
        return chart

    def _gantt_options(self, options):
        opt = ''
        opt += 'g.setShowRes(%s);\n' % options['res']
        opt += 'g.setShowDur(%s);\n' % options['dur']
        opt += 'g.setShowComp(%s);\n' % options['comp']
        w = options['lwidth']
        if w:
            opt += 'g.setLeftWidth(%s);\n' % w
            

        opt += 'g.setCaptionType("%s");\n' % options['caption']

        opt += 'g.setShowStartDate(%s);\n' % options['startDate']
        opt += 'g.setShowEndDate(%s);\n' % options['endDate']

        opt += 'g.setDateInputFormat("%s");\n' % self.jsDateFormat

        opt += 'g.setDateDisplayFormat("%s");\n' % options['dateDisplay']

        opt += 'g.setFormatArr("day","week","month","quarter");\n'
        opt += 'g.setPopupFeatures("location=1,scrollbars=1");\n'
        return opt

    # TODO - use ticket-classN styles instead of colors?
    def _add_sample_tasks(self):
        tasks = ''
        tasks = 'g.setDateInputFormat("mm/dd/yyyy");'

        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(1,   "Define Chart API",     "",          "",          "#ff0000", "http://help.com", 0, "Brian",     0, 1, 0, 1));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(11,  "Chart Object",         "2/20/2011", "2/20/2011", "#ff00ff", "http://www.yahoo.com", 1, "Shlomy",  100, 0, 1, 1));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(12,  "Task Objects",         "",          "",          "#00ff00", "", 0, "Shlomy",   40, 1, 1, 1));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(121, "Constructor Proc",     "2/21/2011", "3/9/2011",  "#00ffff", "http://www.yahoo.com", 0, "Brian T.", 60, 0, 12, 1));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(122, "Task Variables",       "3/6/2011",  "3/11/2011", "#ff0000", "http://help.com", 0, "",         60, 0, 12, 1,121));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(123, "Task Functions",       "3/9/2011",  "3/29/2011", "#ff0000", "http://help.com", 0, "Anyone",   60, 0, 12, 1, 0, "This is another caption"));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(2,   "Create HTML Shell",    "3/24/2011", "3/25/2011", "#ffff00", "http://help.com", 0, "Brian",    20, 0, 0, 1,122));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(3,   "Code Javascript",      "",          "",          "#ff0000", "http://help.com", 0, "Brian",     0, 1, 0, 1 ));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(31,  "Define Variables",     "2/25/2011", "3/17/2011", "#ff00ff", "http://help.com", 0, "Brian",    30, 0, 3, 1, 0,"Caption 1"));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(32,  "Calculate Chart Size", "3/15/2011", "3/24/2011", "#00ff00", "http://help.com", 0, "Shlomy",   40, 0, 3, 1));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(33,  "Draw Taks Items",      "",          "",          "#00ff00", "http://help.com", 0, "Someone",  40, 1, 3, 1));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(332, "Task Label Table",     "3/6/2011",  "3/11/2011", "#0000ff", "http://help.com", 0, "Brian",    60, 0, 33, 1));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(333, "Task Scrolling Grid",  "3/9/2011",  "3/20/2011", "#0000ff", "http://help.com", 0, "Brian",    60, 0, 33, 1));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(34,  "Draw Task Bars",       "",          "",          "#990000", "http://help.com", 0, "Anybody",  60, 1, 3, 1));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(341, "Loop each Task",       "3/26/2011", "4/11/2011", "#ff0000", "http://help.com", 0, "Brian",    60, 0, 34, 1, "332,333"));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(342, "Calculate Start/Stop", "4/12/2011", "5/18/2011", "#ff6666", "http://help.com", 0, "Brian",    60, 0, 34, 1));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(343, "Draw Task Div",        "5/13/2011", "5/17/2011", "#ff0000", "http://help.com", 0, "Brian",    60, 0, 34, 1));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(344, "Draw Completion Div",  "5/17/2011", "6/04/2011", "#ff0000", "http://help.com", 0, "Brian",    60, 0, 34, 1));\n'
        tasks += 'g.AddTaskItem(new JSGantt.TaskItem(35,  "Make Updates",         "10/17/2011","12/04/2011","#f600f6", "http://help.com", 0, "Brian",    30, 0, 3,  1));\n'
        return tasks

    # Get the required columns for the tickets which match the
    # criteria in options.
    def _query_tickets(self, options):
        # Parents is a list of strings
        def _children(parents):
            if len(parents) == 0:
                return []

            parent_list = [self.parent_format % id for id in parents]
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT t.id "
                           "FROM ticket AS t "
                           "LEFT OUTER JOIN ticket_custom AS p ON "
                           "    (t.id=p.ticket AND p.name='%s') "
                           "WHERE p.value IN (%s)" % 
                           (self.fields['parent'],
                            "'" + "','".join(parent_list) + "'"))
            children = ['%s'%row[0] for row in cursor] 

            return parents + _children(children)

        query_args = {}
        for key in options.keys():
            if not key in self.options:
                query_args[key] = options[key]

        if options['root']:
            if options['root'] == 'self':
                this_ticket = self._this_ticket()
                if this_ticket:
                    parents = [ this_ticket ]
                    query_args['id'] = '|'.join(_children(parents))
            else:
                parents = options['root'].split('|')
                query_args['id'] = '|'.join(_children(parents))

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
        for field in self.fields:
            if self.fields[field]:
                fields.append(self.fields[field])

        # Make sure the coloring field is included
        if 'colorBy' in options and options['colorBy'] not in fields:
            fields.append(options['colorBy'])

        # Make the query argument
        query_args['col'] = "|".join(fields)  

        # Construct the querystring. 
        query_string = '&'.join(['%s=%s' % 
                                 item for item in query_args.iteritems()]) 

        # Get the Query Object. 
        query = Query.from_string(self.env, query_string)

 	rawtickets = query.execute(self.req) # Get all tickets 

 	# Do permissions check on tickets 
 	tickets = [t for t in rawtickets  
                   if 'TICKET_VIEW' in self.req.perm('ticket', t['id'])] 

        return tickets

    # Process the tickets to make displaying easy.
    def _process_tickets(self):
        # ChildTicketsPlugin puts '#' at the start of the parent
        # field.  Strip it for simplicity.
        for t in self.tickets:
            if self.fields['parent']:
                parent = t[self.fields['parent']]
                if len(parent) > 0 and parent[0] == '#':
                    t[self.fields['parent']] = parent[1:]

        for t in self.tickets:
            # Clean up custom fields which might be null ('--') vs. blank ('')
            nullable = [ 'pred', 'succ', 
                         'start', 'finish', 
                         'parent', 
                         'worked', 'estimate', 'percent' ]
            for field in nullable:
                if self.fields.get(field) and t[self.fields[field]] == '--':
                    t[self.fields[field]] = ''

            # Get list of children
            if self.fields['parent']:
                if t[self.fields['parent']] == '':
                    t[self.fields['parent']] = 0
                
                t['children'] = [c['id'] for c in self.tickets \
                                     if c[self.fields['parent']] == str(t['id'])]
            else:
                t['children'] = None

            t['link'] = self.req.href.ticket(t['id'])

        for t in self.tickets:
            lists = [ 'pred', 'succ' ]
            for field in lists:
                if self.fields.get(field):
                    if t[self.fields[field]] == '':
                        t[self.fields[field]] = []
                    else:
                        t[self.fields[field]] = t[self.fields[field]].split(',')



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
            if self.ticketsByID[id]['children']:
                # Add another level
                wbs.append(1)
                for c in self.ticketsByID[id]['children']:
                    wbs = _setLevel(c, wbs, level+1)
                # Remove the level we added
                wbs.pop()
            

            # Increment last element of wbs
            wbs[len(wbs)-1] += 1

            return wbs

        # Set WBS and level on all top level tickets (and recurse)
        # If a ticket's parent is in the viewed tickets, consider it top-level
        wbs = [ 1 ]
        for t in self.tickets:
            if not self.fields['parent'] \
                    or t[self.fields['parent']] == 0 \
                    or int(t[self.fields['parent']]) \
                    not in self.ticketsByID.keys():
                wbs = _setLevel(t['id'], wbs, 1)


    def _calc_end(self):      
        for t in self.tickets:
            if t['children']:
                min = None
                for i in t['children']:
                    if min == None:
                        min = self.ticketsByID[i]['calc_finish']
                    else:
                        if self.ticketsByID[i]['calc_finish'] < min:
                            min = self.ticketsByID[i]['calc_finish']
                t['tempEnd'] = min
            else:
                t['tempEnd'] = t['calc_finish']

    def _schedule_tasks(self):
        def _workDays(ticket):
            if self.fields['estimate'] \
                    and ticket[self.fields['estimate']] != '':
                hours = float(ticket[self.fields['estimate']])
                days = int(hours * self.dpe)
                # FIXME - if worked configured and available and
                # greater than estimate, use it instead.
            else:
                # FIXME = make this default duration configurable?
                days = 1

            return days

        def _calendarOffset(days, fromDate):
            # Figure out weeks from days
            weeks = int(days / 7.0)
            # For each week, adjust days for weekends
            days += weeks * 2

            # Get day of week from fromDate; 0 = Monday .. 6 = Sunday
            dow = fromDate.weekday()
            # If new dow ends up in a weekend, adjust by weekend length
            if ((dow + days) % 7) > 4:
                if days > 0:
                    days += 2
                else:
                    days -= 2
                
            return timedelta(days=days)            


        # Return task start as a date string in the format jsGantt.js
        # expects it.
        def _start(ticket):
            # Milestones have no duration, start on their finish date.
            if ticket['type'] == self.milestoneType:
                start = datetime.datetime(*time.strptime(_finish(ticket), self.pyDateFormat)[0:7])
            # If we have a start, parse it
            elif self.fields['start'] and ticket[self.fields['start']] != '':
                start = datetime.datetime(*time.strptime(ticket[self.fields['start']], self.dbDateFormat)[0:7])
            # Otherwise, make it from finish
            else:
                finish = datetime.datetime(*time.strptime(_finish(ticket), self.pyDateFormat)[0:7])
                days = _workDays(ticket)
                start = finish + _calendarOffset(-1*days, finish)

            return start.strftime(self.pyDateFormat)
            

        # TODO: If we have start and estimate, we can figure out
        # finish (opposite case of figuring out start from finish and
        # estimate as we do now).  

        # Return task finish as a date string in the format jsGantt.js
        # expects it.
        def _finish(ticket):
            # If we have a finish, parse it
            if self.fields['finish'] and ticket[self.fields['finish']] != '':
                finish = datetime.datetime(*time.strptime(ticket[self.fields['finish']], self.dbDateFormat)[0:7])                
            # If there are successors, this ticket's finish is the earliest
            # start of any successor
            elif self.fields['succ'] and ticket[self.fields['succ']] != []: 
                finish = None
                for tid in ticket[self.fields['succ']]:
                    if int(tid) in self.ticketsByID:
                        succ = self.ticketsByID[int(tid)]
                        if succ['type'] == self.milestoneType:
                            f = datetime.datetime(*time.strptime(succ[self.fields['finish']], self.dbDateFormat)[0:7])
                            if finish == None or finish > f:
                                finish = f
                if finish == None:
                    finish = date.today()
            # Otherwise, default to today.
            else:
                finish = date.today()

            return finish.strftime(self.pyDateFormat)
        
        # FIXME - do this from milestones back to start
        for t in self.tickets:
            t['calc_start'] = _start(t)
            t['calc_finish'] = _finish(t)


    # Add tasks for milestones related to the tickets
    def _add_milestones(self, options):
        if options.get('milestone'):
            milestones = options['milestone'].split('|')
        else:
            milestones = []

        for t in self.tickets:
            if t['milestone'] != '' and t['milestone'] not in milestones:
                milestones.append(t['milestone'])

        self.firstMilestoneID = 9999

        # Need a unique ID for each task.
        if len(milestones) > 0:
            id = self.firstMilestoneID
            for t in self.tickets:
                if t['id'] > id:
                    id = t['id']
            self.firstMilestoneID = id+1

            # Get the milestones and their due dates
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT name, due FROM milestone " +
                           "WHERE name in ('" + "','".join(milestones) + "')")
            for row in cursor:
                milestoneTicket = {}
                id = id+1
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
                
                # If there's no due date, default to today
                ts = row[1] or None
                milestoneTicket[self.fields['finish']] = \
                    format_date(ts, self.dbDateFormat)

                # jsGantt ignores start for a milestone but we use it
                # for scheduling.
                milestoneTicket[self.fields['start']] = \
                    milestoneTicket[self.fields['finish']]
                # There is no percent complete for a milestone
                milestoneTicket[self.fields['percent']] = 0
                # A milestone has no children or parent
                milestoneTicket['children'] = None
                if self.fields['parent']:
                    milestoneTicket[self.fields['parent']] = 0
                # Link to the milestone page
                milestoneTicket['link'] = self.req.href.milestone(row[0])
                # A milestone has no priority
                milestoneTicket['priority'] = 'n/a'

                # Any ticket with this as a milestone and no
                # successors has the milestone as a successor
                if self.fields['pred'] and self.fields['succ']:
                    pred = []
                    for t in self.tickets:
                        if not t['children'] and \
                                t['milestone'] == row[0] and \
                                t[self.fields['succ']] == []:
                            t[self.fields['succ']] = [ str(id) ]
                            pred.append(str(t['id']))
                    milestoneTicket[self.fields['pred']] = pred
                
                self.tickets.append(milestoneTicket)

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
    #   percent - integer percent complete, 0..100
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
            if ticket['type'] == self.milestoneType:
                owner_name = ''
            elif ticket['owner'] in self.user_map:
                owner_name = self.user_map[ticket['owner']]
            else:
                owner_name = ticket['owner']
            return owner_name
            
        # FIXME - perhaps a closed ticket should always be 100% done.
        def _percent(ticket):
            # Closed tickets are 100% complete
            if ticket['status'] == 'closed':
                percent = 100
            # Compute percent complete if given estimate and worked
            elif self.fields['estimate'] and self.fields['worked']:
                # Try to compute the percent complete, default to 0
                try:
                    worked = float(ticket[self.fields['worked']])
                    estimate = float(ticket[self.fields['estimate']])
                    percent = int(100 * worked / estimate)
                except:
                    # Don't bother logging because 0 for an estimate is common.
                    percent = 0
            # Use percent if provided
            elif self.fields.get('percent'):
                self.env.log.debug('Parsing percent complete from %s' %
                                   self.fields['percent'])
                try:
                    percent = int(ticket[self.fields['percent']])
                except:
                    percent = 0
            # If no estimate and worked (above) and no percent, it's 0
            else:
                percent = 0

            return percent

        def _safeStr(str):
            # No new lines
            str = str.replace('\r\n','\\n')
            # Quoted quotes
            str = str.replace("'","\\'")
            str = str.replace('"','\\"')
            return str

        task = ''

        # pID, pName
        if ticket['type'] == self.milestoneType:
            if ticket['id'] < self.firstMilestoneID:
                # Put ID number on inchpebbles
                name = 'MS:%s (#%s)' % (ticket['summary'], ticket['id'])
            else:
                # Don't show bogus ID of milestone pseudo tickets.
                name = 'MS:%s' % ticket['summary']
        else:
            name = "#%d:%s (%s %s)" % \
                (ticket['id'], ticket['summary'], 
                 ticket['status'], ticket['type'])
        task += 't = new JSGantt.TaskItem(%d,"%s",' % (ticket['id'], _safeStr(name))

        # pStart, pEnd
        task += '"%s",' % ticket['calc_start']
        task += '"%s",' % ticket['calc_finish']

        # pDisplay
        task += '"%s",' % self._task_display(ticket, options)

        # pLink
        task += '"%s",' % ticket['link']

        # pMile
        if ticket['type'] == self.milestoneType:
            task += '1,'
        else:
            task += '0,'

        # pRes (owner)
        task += '"%s",' % _owner(ticket)

        # pComp (percent complete); integer 0..100
        task += '%d,' % _percent(ticket)

        # pGroup (has children)
        if ticket['children']:
            task += '%s,' % 1
        else:
            task += '%s,' % 0
        
        # pParent (parent task ID) 
        if self.fields['parent']:
            task += '%s,' % ticket[self.fields['parent']]
        else:
            task += '%s,' % 0

        # open
        if ticket['level'] < options['openLevel']:
            open = 1
        else:
            open = 0
        task += '%d,' % open

        # predecessors
        if self.fields['pred']:
            task += '"%s",' % ','.join(ticket[self.fields['pred']])
        else:
            task += '"%s",' % ','.join('')
        
        # caption 
        # FIXME - this only shows up if caption is set to caption.
        # we're using caption=Resource.  Where can we show (status, type)?
        task += '"%s (%s %s)"' % (_safeStr(ticket['description']), ticket['status'], ticket['type'])

        task += ');\n'
        task += 'g.AddTaskItem(t);\n'
        return task

    def _add_tasks(self, options):
        def _sort_children(a,b):
            if self.ticketsByID[a]['tempEnd'] < self.ticketsByID[b]['tempEnd']:
                return -1
            elif self.ticketsByID[a]['tempEnd'] > self.ticketsByID[b]['tempEnd']:
                return 1
            elif self.ticketsByID[a]['calc_start'] > self.ticketsByID[b]['calc_start']:
                return 1
            else:
                return -1

        if options.get('sample'):
            tasks = self._add_sample_tasks()
        else:
            tasks = ''
            self.tickets = self._query_tickets(options)

            # Post process the query to add and compute fields so
            # displaying the tickets is easy
            self._process_tickets()

            # Add the milestone(s) with all their tickets depending on them.
            self._add_milestones(options)

            # Faster lookups for WBS and scheduling.
            self.ticketsByID = {}
            for t in self.tickets:
                self.ticketsByID[t['id']] = t

            self._schedule_tasks()
            self._calc_end()
            self.tickets.sort(key=itemgetter('calc_start'))            
            self.tickets.sort(key=itemgetter('tempEnd'))            

            for i in self.tickets:
                if i['children']:
                    i['children'].sort(_sort_children)
            self._compute_wbs()                
            self.tickets.sort(key=itemgetter('wbs'))

            for ticket in self.tickets:
                tasks += self._format_ticket(ticket, options)

        return tasks

    def _parse_options(self, content):
        _, options = parse_args(content, strict=False)

        for opt in self.options.keys():
            if opt in options:
                if isinstance(self.options[opt], (int, long)):
                    options[opt] = int(options[opt])
            else:
                options[opt] = self.options[opt]

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
