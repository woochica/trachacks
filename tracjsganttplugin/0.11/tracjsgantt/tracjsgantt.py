from datetime import timedelta, date, datetime
from estimationtools.utils import parse_options, execute_multiquery, get_estimation_field, get_actual_field, get_estimation_suffix, get_closed_states, get_assumed_estimate, get_additional_hours

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


class TaacJSGanttSupport(Component):
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
            'res': '1',
            'dur': '1',
            'comp': '1',
            'caption': 'Resource',
            'startDate': '1',
            'endDate': '1',
            'dateDisplay': 'mm/dd/yyyy',
            'openLevel': 999,
            }

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

        # Cache enum lookups (just priority for now)
        # TODO - get all enums, at least severity
        self.p_values = {}
        self.enums = {}
        self.enums['priority_value'] = 'priority'

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT name," + 
                       db.cast('value', 'int') + 
                       " FROM enum WHERE type=%s", ('priority',))
        for name, value in cursor:
            self.p_values[name] = value
    
    def _begin_gantt(self, options):
        if options.get('format'):
            format = options['format']
        else:
            format = 'day'

        text = ''
        text += '<div style="position:relative" class="gantt" id="GanttChartDIV"></div>\n'
        text += '<script language="javascript">\n'
        text += 'var g = new JSGantt.GanttChart("g",document.getElementById("GanttChartDIV"), "%s");\n' % format
        text += 'var t;\n'
        return text

    def _end_gantt(self):
        chart = ''
        chart += 'g.Draw();\n'
        chart += 'g.DrawDependencies();\n'
        chart += '</script>\n'
        return chart

    def _gantt_options(self, options):

        def g(name):
            return (options[name] if options.get(name) else self.options[name])

        opt = ''
        opt += 'g.setShowRes(%s);\n' % g('res')
        opt += 'g.setShowDur(%s);\n' % g('dur')
        opt += 'g.setShowComp(%s);\n' % g('comp')

        opt += 'g.setCaptionType("%s");\n' % g('caption')

        opt += 'g.setShowStartDate(%s);\n' % g('startDate')
        opt += 'g.setShowEndDate(%s);\n' % g('endDate')

        opt += 'g.setDateInputFormat("%s");\n' % self.pyDateFormat

        opt += 'g.setDateDisplayFormat("%s");\n' % g('dateDisplay')

        opt += 'g.setFormatArr("day","week","month","quarter");\n'
        return opt

    def _add_sample_tasks(self):
        tasks = ''
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

    # Get the required columns for the tickets which match the criteria in options.
    def _query_tickets(self, options):
        query_args = {}
        for key in options.keys():
            if not key in self.options:
                query_args[key] = options[key]

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
    def _process_tickets(self, tickets):
        for t in tickets:
            # Clean up custom fields which might be null ('--') vs. blank ('')
            nullable = [ 'pred', 'succ', 'start', 'finish', 'parent', ]
            for field in nullable:
                if self.fields.get(field) and t[self.fields[field]] == '--':
                    t[self.fields[field]] = ''

            # Get list of children
            if self.fields['parent']:
                if t[self.fields['parent']] == '':
                    t[self.fields['parent']] = 0
                
                t['children'] = [c['id'] for c in tickets \
                                     if c[self.fields['parent']] == str(t['id'])]
            else:
                t['children'] = None

            # Compute percent complete if given estimate and worked
            if self.fields['estimate'] and self.fields['worked']:
                self.fields['percent'] = 'percent'
                # Try to compute the percent complete, default to 0
                try:
                    w = float(t[self.fields['worked']])
                    e = float(t[self.fields['estimate']])
                    t[self.fields['percent']] = int(100 * w / e)
                except:
                    # Don't bother logging because 0 for an estimate is common.
                    t[self.fields['percent']] = 0
            # If no estimate and worked (above) and no percent, create a field
            elif not self.fields.get('percent'):
                self.fields['percent'] = 'percent'
                

            # Make sure there's a percent complete value
            if self.fields['percent'] and not t.get('percent'):
                t[self.fields['percent']] = 0

            # If there's no finish, set it to today (in db format,
            # convert below)
            if self.fields['finish']:
                if t[self.fields['finish']] == '':
                    t[self.fields['finish']] = \
                        date.today().strftime(self.dbDateFormat)

            # If there's no start, set it to finish - 1 day.
            if self.fields['start']:
                if t[self.fields['start']] == '':
                    finish = datetime.strptime(t[self.fields['finish']],
                                               self.dbDateFormat)
                    # FIXME - make the default length configurable
                    delta = timedelta(days=-1)
                    start = finish + delta
                    t[self.fields['start']] = start.strftime(self.dbDateFormat)
                
            # Convert start and finish times from Trac db format to
            # jsGantt format
            for field in ['start', 'finish']:
                if self.fields[field]:
                    d = datetime.strptime(t[self.fields[field]],
                                          self.dbDateFormat)
                    t[self.fields[field]] = d.strftime(self.pyDateFormat)
            

            t['link'] = '/trac/ticket/%d' % t['id']

            # FIXME - translate owner to full name

        # Figure out the tickets' levels for controlling how many levels are open
        tarr = {}
        for t in tickets:
            tarr[t['id']] = t

        # Set the ticket's level then recurse to children.
        def _setLevel(id, level):
            tarr[id]['level'] = level
            if tarr[id]['children']:
                for c in tarr[id]['children']:
                    _setLevel(c, level+1)

        # Set level on all top level tickets (and recurse)
        for t in tickets:
            if not self.fields['parent'] or t[self.fields['parent']] == 0:
                _setLevel(t['id'], 1)

    # Add tasks for milestones related to the tickets
    def _add_milestones(self, tickets, options):
        if options.get('milestone'):
            milestones = options['milestone'].split('|')
        else:
            milestones = []

        for t in tickets:
            if t['milestone'] != '' and t['milestone'] not in milestones:
                milestones.append(t['milestone'])

        if len(milestones) > 0:
            # Need a unique ID for each task.
            id = 9999
            for t in tickets:
                if t['id'] > id:
                    id = t['id']

            # Get the milestones and their due dates
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT name, due FROM milestone "
                           "WHERE name in ('" + "','".join(milestones) + "')")
            for row in cursor:
                ticket = {}
                id = id+1
                ticket['id'] = id
                ticket['summary'] = row[0]
                ticket['description'] = 'Milestone %s' % row[0]
                ticket['milestone'] = row[0]
                # A milestone has no owner
                ticket['owner'] = ''
                ticket['type'] = self.milestoneType
                ticket['status'] = ''
                # Milestones are always shown
                ticket['level'] = 0

                us = row[1]
                # If there's no due date, default to today
                if us == 0:
                    finish = date.today()
                else:
                    s = us / 1000000
                    finish = date.fromtimestamp(s)
                ticket[self.fields['finish']] = \
                    finish.strftime(self.pyDateFormat)

                # Start is ignored for a milestone.
                ticket[self.fields['start']] = ticket[self.fields['finish']]
                # There is no percent complete for a milestone
                ticket['percent'] = 0
                # A milestone has no children or parent
                ticket['children'] = None
                if self.fields['parent']:
                    ticket[self.fields['parent']] = 0
                # Link to the milestone page
                ticket['link'] = '/trac/milestone/%s' % row[0]
                # A milestone has no priority
                ticket['priority'] = 'n/a'

                # Any ticket with this as a milestone and no
                # successors has the milestone as a successor
                if self.fields['pred'] and self.fields['succ']:
                    pred = []
                    for t in tickets:
                        if not t['children'] and \
                                t['milestone'] == row[0] and \
                                t[self.fields['succ']] == '':
                            t[self.fields['succ']] = str(id)
                            pred.append(str(t['id']))
                    ticket[self.fields['pred']] = ','.join(pred)

                tickets.append(ticket)

        

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
    def _format_ticket(self, t, options):
        def _safeDesc(d):
            return d.replace('\r\n','\\n')

        task = ''

        # pID, pName
        if t['type'] == self.milestoneType:
            name = t['summary']
        else:
            name = "#%d:%s" % (t['id'], t['summary'])
        task += 't = new JSGantt.TaskItem(%d,"%s",' % (t['id'], name)

        # pStart, pEnd
        if self.fields['finish']:
            f = datetime.strptime(t[self.fields['finish']],self.dbDateFormat)
        else:
            f = date.today()
        delta = timedelta(days=-1)
        s = f + delta
        s = s.strftime(self.pyDateFormat)
        f = f.strftime(self.pyDateFormat)
        task += '"%s",' % (t[self.fields['start']] if self.fields['start'] else s)
        task += '"%s",' % (t[self.fields['finish']] if self.fields['finish'] else f)

        # pDisplay
        # TODO - it'd be nice to color by owner or milestone or severity
        if t['priority'] in self.p_values:
            display = 'class=ticket-class%d' % self.p_values[t['priority']]
        else:
            display = '#ff7f3f'

        task += '"%s",' % display

        # pLink
        task += '"%s",' % t['link']

        # pMile
        if t['type'] == self.milestoneType:
            task += '1,'
        else:
            task += '0,'

        # pRes (owner)
        task += '"%s",' % t['owner']

        # pComp (percent complete); integer 0..100
        task += '%d,' % int(t[self.fields['percent']])

        # pGroup (has children)
        task += '%s,' % (1 if t['children'] else 0)

        # pParent (parent task ID) 
        task += '%s,' % \
            (t[self.fields['parent']] if self.fields['parent'] else 0)

        # open
        if t['level'] < options['openLevel']:
            open = 1
        else:
            open = 0
        task += '%d,' % open

        # predecessors
        task += '"%s",' % t[self.fields['pred']] if self.fields['pred'] else ''

        # caption 
        # FIXME - this only shows up if caption is set to caption.
        # we're using caption=Resource.  Where can we show (status, type)?
        task += '"%s (%s %s)"' % (_safeDesc(t['description']), t['status'], t['type'])

        task += ');\n'
        task += 'g.AddTaskItem(t);\n'
        return task

    def _add_tasks(self, options):
        if options.get('sample'):
            tasks = self._add_sample_tasks()
        else:
            tasks = ''
            tickets = self._query_tickets(options)

            # Post process the query to add and compute fields so
            # displaying the tickets is easy
            self._process_tickets(tickets)

            # Add the milestone(s) with all their tickets depending on them.
            self._add_milestones(tickets, options)

            for ticket in tickets:
                tasks += self._format_ticket(ticket, options)

        return tasks

    def _parse_options(self, content):
        _, options = parse_args(content, strict=False)

        if options.get('openLevel'):
            options['openLevel'] = int(options['openLevel'])
        else:
            options['openLevel'] = self.options['openLevel']
        
        return options
        
    # 
    def expand_macro(self, formatter, name, content):
        self.req = formatter.req

        options = self._parse_options(content)
        chart = ''
        tasks = self._add_tasks(options)
        if len(tasks) == 0:
            chart += 'No tasks selected.'
        else:
            chart += self._begin_gantt(options)
            chart += self._gantt_options(options)
            chart += tasks
            chart += self._end_gantt()

        return chart
