import re
import time
from datetime import timedelta, datetime
from operator import itemgetter, attrgetter

from trac.util.html import Markup
from trac.util.text import javascript_quote
from trac.wiki.macros import WikiMacroBase
from trac.web.chrome import Chrome
import copy
from trac.ticket.query import Query

from trac.config import IntOption, Option
from trac.core import implements, Component, TracError
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from pkg_resources import resource_filename

from trac.wiki.api import parse_args

from tracpm import TracPM
# ========================================================================
class TracJSGanttSupport(Component):
    implements(IRequestFilter, ITemplateProvider)
    
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

Site-wide defaults for macro arguments may be set in the `trac-jsgantt` section of `trac.ini`.  `option.<opt>` overrides the built-in default for `<opt>` from the table above.

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
        text += '<div style="position:relative" class="gantt" ' + \
            'id="GanttChartDIV_'+self.GanttID+'"></div>\n'
        text += '<script language="javascript">\n'
        text += 'var '+self.GanttID+' = new JSGantt.GanttChart("'+ \
            self.GanttID+'",document.getElementById("GanttChartDIV_'+ \
            self.GanttID+'"), "%s", "%s");\n' % \
            (javascript_quote(defaultFormat), showdep)
        text += 'var t;\n'
        text += 'if (window.addEventListener){\n'
        text += '  window.addEventListener("resize", ' + \
            'function() { ' + self.GanttID+'.Draw(); '
        if options['showdep']:
            text += self.GanttID+'.DrawDependencies();'
        text += '}, false);\n'
        text += '} else {\n'
        text += '  window.attachEvent("onresize", ' + \
            'function() { '+self.GanttID+'.Draw(); '
        if options['showdep']:
            text += self.GanttID+'.DrawDependencies();'
        text += '}, false);\n'
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

        # Add configured PM fields
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
        if t1['id'] in self.pm.successors(t2):
            return 1
        # If t1 depends on t2, t1 is first
        elif t2['id'] in self.pm.successors(t1):
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
        

    # Format a ticket into JavaScript source to display the
    # task. ticket is expected to have:
    #   children - child ticket IDs or None
    #   description - ticket description.
    #   id - ticket ID, an integer
    #   level - levels from root (0)
    #   link - What to link to
    #   owner - Used as resource name.
    #   percent - integer percent complete, 0..100 (or "act/est")
    #   priority - used to color the task
    #   calc_finish - end date (ignored if children is not None)
    #   self.fields[parent] - parent ticket ID
    #   self.fields[pred] - predecessor ticket IDs
    #   calc_start - start date (ignored if children is not None)
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
        task += '"%s",' % self.pm.percentComplete(ticket)

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
        elif options['root'] and \
                str(ticket['id']) in options['root'].split('|'):
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
        pred = [str(s) for s in self.pm.predecessors(ticket)]
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
