from datetime import timedelta
from estimationtools.utils import *
from trac.core import TracError
from trac.util.html import Markup
from trac.wiki.macros import WikiMacroBase
import copy

DEFAULT_OPTIONS = {'width': '800', 'height': '200', 'color': 'ff9900'}

class BurndownChart(WikiMacroBase):
    """Creates burn down chart for selected tickets.

    This macro creates a chart that can be used to visualize the progress in a milestone (e.g., sprint or 
    product backlog). 
    For a given set of tickets and a time frame, the remaining estimated effort is calculated.
    
    The macro has the following parameters:
     * a comma-separated list of query parameters for the ticket selection, in the form "key=value" as specified in TracQuery#QueryLanguage.
     * `startdate`: '''mandatory''' parameter that specifies the start date of the period (ISO8601 format)
     * `enddate`: end date of the period. If omitted, it defaults to either the milestones (if given) `completed' date, 
       or `due` date, or today (in that order) (ISO8601 format)
     * `width`: width of resulting diagram (defaults to 800)
     * `height`: height of resulting diagram (defaults to 200)
     * `color`: color specified as 6-letter string of hexadecimal values in the format `RRGGBB`.
       Defaults to `ff9900`, a nice orange.
     
    Examples:
    {{{
        [[BurndownChart(milestone=Sprint 1, startdate=2008-01-01)]]
        [[BurndownChart(milestone=Release 3.0|Sprint 1, startdate=2008-01-01, enddate=2008-01-15,
            width=600, height=100, color=0000ff)]]
    }}}
    """

    estimation_field = get_estimation_field()
    
    def render_macro(self, req, name, content):
        # prepare options
        options, query_args = parse_options(self.env.get_db_cnx(), content, copy.copy(DEFAULT_OPTIONS))

        if not options['startdate']:
            raise TracError("No start date specified!")
               
        # calculate data
        timetable = self._calculate_timetable(options, query_args, req)
        
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
            
        title = ''
        if options.get('milestone'):
            title = options['milestone'].split('|')[0]
                
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
                  "|".join(weekends), options['color'], title))
                
    def _calculate_timetable(self, options, query_args, req):
        db = self.env.get_db_cnx()

        # create dictionary with entry for each day of the required time period
        timetable = {}
        
        currentdate = options['startdate']
        while currentdate <= options['enddate']:
            timetable[currentdate] = 0.0
            currentdate += timedelta(days=1)

        # get current values for all tickets within milestone and sprints     
        
        query_args[self.estimation_field + "!"] = None
        tickets = execute_query(self.env, req, query_args)

        # print tickets

        for t in tickets:
            creationdate = t['time'].date()
            estimation = t[self.estimation_field]
            
            # get change history for each ticket
            history_cursor = db.cursor()
            history_cursor.execute("SELECT " 
                "DISTINCT c.time AS time, c.oldvalue as oldvalue " 
                "FROM ticket t, ticket_change c "
                "WHERE t.id = %s and c.ticket = t.id and c.field=%s "
                "ORDER BY c.time DESC", [t['id'], self.estimation_field])
            
            nextchangedate = None
            nextvalue = None 
            row = history_cursor.fetchone()
            if row:
                nextchangedate = datetime.fromtimestamp(row[0], utc).date()
                nextvalue = row[1]

            # iterate backwards through period and add estimations
            currentdate = options['enddate']
            while currentdate >= options['startdate'] and currentdate >= creationdate:
                # go back through history until we have the proper value
                while nextchangedate and nextchangedate > currentdate:
                    estimation = nextvalue
                    row = history_cursor.fetchone()
                    if row:
                        nextchangedate = datetime.fromtimestamp(row[0], utc).date()
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
    
        
        
        

