from datetime import timedelta
from estimationtools.utils import *
from trac.core import TracError
from trac.util.html import Markup
from trac.wiki.macros import WikiMacroBase
import copy
import re

DEFAULT_OPTIONS = {'width': '800', 'height': '200', 'color': 'ff9900'}

class BurndownChart(WikiMacroBase):
    """Creates burn down chart for given milestone.

    This macro creates a chart that can be used to visualize the progress in a milestone (aka sprint or 
    product backlog). 
    For a given milestone and time frame, the remaining, estimated effort is calculated.
    
    The macro has the following parameters:
     * `milestone`: '''mandatory''' parameter that specifies the milestone.
     * `startdate`: '''mandatory''' parameter that specifies the start date of the period (ISO8601 format)
     * `enddate`: end date of the period. If omitted, it defaults to either the milestones `completed' date, 
       or `due`date, or today (in that order) (ISO8601 format)
     * `sprints`: list of comma-separated name of sprints to be included in calculation. Must be surrounded by
       brackets.
     * `width`: width of resulting diagram (defaults to 800)
     * `height`: height of resulting diagram (defaults to 200)
     * `color`: color specified as 6-letter string of hexadecimal values in the format `RRGGBB`.
       Defaults to `ff9900`, a nice orange.
     
    Examples:
    {{{
        [[BurndownChart(milestone = Sprint 1, startdate = 2008-01-01)]]
        [[BurndownChart(milestone = Release 3.0, startdate = 2008-01-01, enddate = 2008-01-15,
            width = 600, height = 100, color = 0000ff, sprints = (Sprint 1, Sprint 2))]]
    }}}
    """

    estimation_field = get_estimation_field()
    
    def render_macro(self, req, name, content):
        # you need 'TICKT_VIEW' or 'TICKET_VIEW_CC' (see PrivateTicketPatch) permissions
        if not (req.perm.has_permission('TICKET_VIEW') or 
                req.perm.has_permission('TICKET_VIEW_CC')):
            raise TracError('TICKET_VIEW or TICKET_VIEW_CC permission required')
        options = copy.copy(DEFAULT_OPTIONS)
        
        # replace all ',' in brackets with ';' to avoid splitting list of sprints
        def repl(match):
            return match.group().replace(',', ';')
        regexp = re.compile(r'\((.*)\)')
        content = regexp.sub(repl, content)
        
        if content:
            for arg in content.split(','):
                i = arg.index('=')
                options[arg[:i].strip()] = arg[i + 1:].strip()

        # prepare options
        options = parse_options(self.env.get_db_cnx(), options)
        if not options['startdate']:
            raise TracError("No start date specified!")
        
        # parse list of sprints
        sprintsarg = options.get('sprints')
        if sprintsarg:
            options['sprints'] = sprintsarg.strip('()').split(';')
        
        # calculate data
        timetable = self._calculate_timetable(options)
        
        # scale data      
        xdata, ydata, maxhours = self._scale_data(timetable, options)
    
        # build html for google chart api
        dates = timetable.keys()
        dates.sort()
        bottomaxis = "0:|" + ("|").join([str(date.day) for date in dates]) + \
            "|1:|%s|%s" % (dates[0].month, dates[ - 1].month) + \
            "|2:|%s|%s" % (dates[0].year, dates[ - 1].year)
        leftaxis = "3,0,%s" % maxhours
        
        # mark weekends
        weekends = []
        saturday = None
        index = 0
        halfday = 0.5 / (len(dates) - 1)
        for date in dates:
            if date.weekday() == 5:
                saturday = index
            if saturday and date.weekday() == 6:
                weekends.append("R,f1f1f1,0,%s,%s" % ((float(xdata[saturday]) / 100) - halfday,
                                                      (float(xdata[index]) / 100) + halfday))
                saturday = None
            index += 1
        # special handling if time period starts with Sundays...
        if len(dates) > 0 and dates[0].weekday() == 6:
            weekends.append("R,f1f1f1,0,0.0,%s" % halfday)
        # or ends with Saturday
        if len(dates) > 0 and dates[ - 1].weekday() == 5:
            weekends.append("R,f1f1f1,0,%s,1.0" % (1.0 - halfday))
                
        return Markup("<img src=\"http://chart.apis.google.com/chart?"
               "chs=%sx%s" 
               "&amp;chd=t:%s|%s"
               "&amp;cht=lxy"
               "&amp;chxt=x,x,x,y"
               "&amp;chxl=%s"
               "&amp;chxr=%s"
               "&amp;chm=%s"
               "&amp;chg=100.0,100.0,1,0"  # create top and right bounding line by using grid
               "&amp;chco=%s"
               "&amp;chtt=%s\" "
               "alt=\'Burndown Chart\' />" 
               % (options['width'], options['height'],
                  ",".join(xdata), ",".join(ydata), bottomaxis, leftaxis,
                  "|".join(weekends), options['color'], options['milestone'].strip('\'\"')))
                
    def _calculate_timetable(self, options):
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # create dictionary with entry for each day of the required time period
        timetable = {}
        
        currentdate = options['startdate']
        while currentdate <= options['enddate']:
            timetable[currentdate] = 0.0
            currentdate += timedelta(days=1)

        # get current values for all tickets within milestone and sprints     
        sprints = options.get('sprints')
        if not sprints:
            sprints = []
            
        sprints = [options['milestone']] + sprints

        select_tickets = ("SELECT "
           "id, time, p.value as estimation "
           "FROM ticket t, ticket_custom p "
           "WHERE p.ticket = t.id and p.name = %%s and (t.milestone in (%s)) "
           "ORDER BY t.id" % (',').join(['%s' for sprint in sprints]))
            
        cursor.execute(select_tickets, [self.estimation_field] + sprints)
        
        for id, time, estimation in cursor:
            creationdate = datetime.fromtimestamp(time).date()
            
            # get change history for each ticket
            history_cursor = db.cursor()
            history_cursor.execute("SELECT " 
                "DISTINCT c.time AS time, c.oldvalue as oldvalue " 
                "FROM ticket t, ticket_change c "
                "WHERE t.id = %s and c.ticket = t.id and c.field=%s "
                "ORDER BY c.time DESC", [id, self.estimation_field])
            
            nextchangedate = None
            nextvalue = None 
            row = history_cursor.fetchone()
            if row:
                nextchangedate = datetime.fromtimestamp(row[0]).date()
                nextvalue = row[1]

            # iterate backwards through period and add estimations
            currentdate = options['enddate']
            while currentdate >= options['startdate'] and currentdate >= creationdate:
                # go back through history until we have the proper value
                while nextchangedate and nextchangedate > currentdate:
                    estimation = nextvalue
                    row = history_cursor.fetchone()
                    if row:
                        nextchangedate = datetime.fromtimestamp(row[0]).date()
                        nextvalue = row[1]
                    else:
                        nextchangedate = None
                        
                try:
                    timetable[currentdate] += float(estimation)
                except:
                    pass
                currentdate -= timedelta(days=1)
       
        return timetable
        
    def _scale_data(self, timetable, options):
        # create sorted list of dates
        dates = timetable.keys()
        dates.sort()

        maxhours = max(timetable.values())
                
        if maxhours <= 0.0:
            maxhours = 100.0
        ydata = [str(timetable[d] * 100 / maxhours) for d in dates]
        xdata = [str(x * 100.0 / (len(dates) - 1)) 
                 for x in range((options['enddate'] - options['startdate']).days + 1)]
        
        # mark ydata invalid that is after today
        if options['enddate'] > options['today']:
            remaining_days = (options['enddate'] - options['today']).days;
            ydata = ydata[: - remaining_days] + ['-1' for x in xrange(0, remaining_days)]
        
        return xdata, ydata, maxhours
    
        
        
        

