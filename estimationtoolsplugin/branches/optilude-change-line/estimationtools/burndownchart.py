from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime
from datetime import timedelta
from estimationtools.utils import parse_options, execute_query
from estimationtools.utils import get_estimation_field, get_closed_states, get_initial_estimation_field
from trac.core import TracError
from trac.util.html import Markup
from trac.util.datefmt import utc
from trac.wiki.macros import WikiMacroBase
import copy

DEFAULT_OPTIONS = {'width': '800', 'height': '200', 'color': 'ff9900,aa8800'}

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
     * `title`: the title of the graph. If omitted, defaults to the title of the first milestone given, if any.
     * `change`: set to 1 to include a second line showing what the burndown would've looked like, had
        there not been any scope change
     * `interval_days`: the number of days between points on the x axis, defaulting to 1
     
    Examples:
    {{{
        [[BurndownChart(milestone=Sprint 1, startdate=2008-01-01)]]
        [[BurndownChart(milestone=Release 3.0|Sprint 1, startdate=2008-01-01, enddate=2008-01-15,
            width=600, height=100, color=0000ff)]]
    }}}
    """

    initial_estimation_field = get_initial_estimation_field()
    estimation_field = get_estimation_field()
    closed_states = get_closed_states()
    
    def render_macro(self, req, name, content):
        
        # prepare options
        options, query_args = parse_options(self.env.get_db_cnx(), content, copy.copy(DEFAULT_OPTIONS))

        if not options['startdate']:
            raise TracError("No start date specified!")
               
        # minimum time frame is one day
        if (options['startdate'] >= options['enddate']):
            options['enddate'] = options['startdate'] + timedelta(days=1)

        change = options['change']

        # calculate data
        timetable, delta = self._calculate_timetable(options, query_args, req)
        timetable_less_change = {}
        
        if change:
            
            cumulative_change = Decimal(0)
            for current_date in sorted(timetable.keys()):
                cumulative_change += delta.get(current_date, Decimal(0))
                timetable_less_change[current_date] = timetable[current_date] - cumulative_change

        dates = sorted(timetable.keys())

        # build html for google chart api

        chart_params = {}
        chart_params['cht'] = 'lxy'
        chart_params['chtt'] = self._get_title(options)
        chart_params['chco'] = options['color']
        chart_params['chs'] = "%sx%s" % (options['width'], options['height'])
        chart_params['chg'] = "100.0,100.0,1,0"  # create top and right bounding line by using grid"
        chart_params['chxt'] = "x,x,x,y"
        
        # Add scaled data
        maxhours = max(timetable.values())
        if change:
            maxhours = max(maxhours, max(timetable_less_change.values()))
        
        xdata, ydata,maxhours = self._scale_data(timetable, dates, maxhours, options)
        chart_params['chd'] = "t:%s|%s" % (",".join(xdata), ",".join(ydata),)
        cxdata = cydata = None
        if change:
            cxdata, cydata,maxhours = self._scale_data(timetable_less_change, dates, maxhours, options)
            chart_params['chd'] += "|%s|%s" % (",".join(cxdata), ",".join(cydata),)
        
        if change:            
            chart_params['chdl'] = "Current|Less change"
        
        # Add axes
        chart_params['chxl'] = "0:|" + "|".join([str(date.day) for date in dates]) + \
            "|1:|%s|%s" % (dates[0].month, dates[ - 1].month) + \
            "|2:|%s|%s" % (dates[0].year, dates[ - 1].year)
        chart_params['chxr'] = "3,0,%s" % maxhours
        
        # Add weekends
        downtime = self._mark_downtime(options, dates, xdata, ydata)
        if downtime:
            chart_params['chm'] = '|'.join(downtime)
        
        return Markup("<img src=\"http://chart.apis.google.com/chart?%s\" alt=\"Burndown Chart\" />" % 
                        "&amp;".join("%s=%s" % (k,v) for k,v in chart_params.items()))

    def _calculate_timetable(self, options, query_args, req):
        db = self.env.get_db_cnx()

        estimation_field = self.estimation_field
        initial_estimation_field = self.initial_estimation_field or estimation_field
        one_field = (estimation_field == initial_estimation_field)

        # create dictionary with entry for each day of the required time period
        timetable = {}
        delta = {}
        
        current_date = options['startdate']
        max_date = current_date
        while current_date <= options['enddate']:
            timetable[current_date] = Decimal(0)
            delta[current_date] = Decimal(0)
            max_date = current_date
            current_date += timedelta(days=options.get('interval_days', 1))

        # Ensure we have today's date in the timetable as well, in case interval_days
        # caused us to stop before it.
        if options['today'] <= options['enddate']:
            timetable[options['today']] = Decimal(0)
            delta[options['today']] = Decimal(0)

        # get current values for all tickets within milestone and sprints     
        
        query_args[estimation_field + "!"] = None
        if estimation_field != initial_estimation_field:
            query_args[initial_estimation_field + "!"] = None
        query_args['status' + "!"] = None
        
        tickets = execute_query(self.env, req, query_args)

        # add the open effort for each ticket for each day to the timetable

        for t in tickets:
            
            # Record the current (latest) status and estimate, and ticket
            # creation date
            
            creation_date = t['time'].date()
            latest_status = t['status']
            latest_estimate = self._cast_estimate(t[estimation_field])
            if not latest_estimate:
                latest_estimate = Decimal(0)
            latest_initial_estimate = self._cast_estimate(t[initial_estimation_field])
            if not latest_initial_estimate:
                latest_initial_estimate = Decimal(0)
            
            # Fetch change history for status and effort fields for this ticket
            history_cursor = db.cursor()
            history_cursor.execute("SELECT " 
                "DISTINCT c.field as field, c.time AS time, c.oldvalue as oldvalue, c.newvalue as newvalue " 
                "FROM ticket t, ticket_change c "
                "WHERE t.id = %s and c.ticket = t.id and (c.field=%s or c.field=%s or c.field='status')"
                "ORDER BY c.time ASC", [t['id'], estimation_field, initial_estimation_field])
            
            # Build up two dictionaries, mapping dates when effort/status
            # changed, to the latest effort/status on that day (in case of
            # several changes on the same day). Also record the oldest known
            # effort/status, i.e. that at the time of ticket creation
            
            estimate_history = {}
            initial_estimate_history = {}
            status_history = {}
            
            earliest_estimate = None
            earliest_initial_estimate = None
            earliest_status = None
            
            for row in history_cursor:
                row_field, row_time, row_old, row_new = row
                event_date = datetime.fromtimestamp(row_time, utc).date()
                if row_field == estimation_field:
                    new_value = self._cast_estimate(row_new)
                    if new_value is not None:
                        estimate_history[event_date] = new_value
                    if earliest_estimate is None:
                        earliest_estimate = self._cast_estimate(row_old)
                # note: not using elif since estimation_field and initial_estimate_field could be the same!
                if row_field == initial_estimation_field:
                    new_value = self._cast_estimate(row_new)
                    if new_value is not None:
                        initial_estimate_history[event_date] = new_value
                    if earliest_initial_estimate is None:
                        earliest_initial_estimate = self._cast_estimate(row_old)
                if row_field == 'status':
                    status_history[event_date] = row_new
                    if earliest_status is None:
                        earliest_status = row_old
            
            # If we don't know already (i.e. the ticket effort/status was 
            # not changed on the creation date), set the effort on the
            # creation date. It may be that we don't have an "earliest"
            # estimate/status, because it was never changed. In this case,
            # use the current (latest) value.
            
            if not creation_date in estimate_history:
                if earliest_estimate is not None:
                    estimate_history[creation_date] = earliest_estimate
                else:
                    estimate_history[creation_date] = latest_estimate
            
            if not creation_date in initial_estimate_history:
                if earliest_initial_estimate is not None:
                    initial_estimate_history[creation_date] = earliest_initial_estimate
                else:
                    initial_estimate_history[creation_date] = latest_initial_estimate
            
            if not creation_date in status_history:
                if earliest_status is not None:
                    status_history[creation_date] = earliest_status
                else:
                    status_history[creation_date] = latest_status
            
            # There is a risk that the history table is messed up. Trust
            # the ticket/ticket_custom tables more.
            
            estimate_history[options['today']] = latest_estimate
            initial_estimate_history[options['today']] = latest_initial_estimate
            status_history[options['today']] = latest_status
            
            # Finally add estimates to the timetable. Treat any period where the
            # ticket was closed as estimate 0. We need to loop from ticket
            # creation date, not just from the timetable start date, since
            # it's possible that the ticket was changed between these two
            # dates.

            current_date = creation_date
            current_estimate = None
            previous_initial_estimate = Decimal(0)
            is_open = None

            while current_date <= options['enddate']:
            
                if current_date in status_history:
                    is_open = (status_history[current_date] not in self.closed_states)
            
                if current_date in estimate_history:
                    current_estimate = estimate_history[current_date]
            
                if current_date in initial_estimate_history:
                    effort_delta = initial_estimate_history[current_date] - previous_initial_estimate
                    if effort_delta != Decimal(0):
                        previous_initial_estimate = initial_estimate_history[current_date]                    
                        if current_date > options['startdate'] and current_date in delta:
                            delta[current_date] += effort_delta

                if current_date in timetable and current_date >= options['startdate'] and is_open:
                    timetable[current_date] += current_estimate
            
                current_date += timedelta(days=1)
        
        return timetable, delta
        
    def _scale_data(self, timetable, dates, maxhours, options):
        # create sorted list of dates
        
        if maxhours <= Decimal(0):
            maxhours = Decimal(100)
        ydata = [str(self._round(timetable[d] * Decimal(100) / maxhours))
                 for d in dates]
        xdata = [str(self._round(x * Decimal(100) / (len(dates) - 1)))
                 for x in range((options['enddate'] - options['startdate']).days + 1)]
        
        # mark ydata invalid that is after today
        if options['enddate'] > options['today']:
            remaining_days = (options['enddate'] - options['today']).days;
            ydata = ydata[: - remaining_days] + ['-1' for x in xrange(0, remaining_days)]
        
        return xdata, ydata, maxhours
    
    def _mark_downtime(self, options, dates, xdata, ydata):
        
        # Only mark weekends if we are showning a day-by-day burndown
        if options.get('interval_days', 1) != 1:
            return []
            
        weekends = []
        saturday = None
        index = 0
        halfday = self._round(Decimal("0.5") / (len(dates) - 1))
        for date in dates:
            if date.weekday() == 5:
                saturday = index
            if saturday and date.weekday() == 6:
                weekends.append("R,f1f1f1,0,%s,%s" % (self._round((Decimal(xdata[saturday]) / 100) - halfday),
                                                      self._round((Decimal(xdata[index]) / 100) + halfday)))
                saturday = None
            index += 1
        # special handling if time period starts with Sundays...
        if len(dates) > 0 and dates[0].weekday() == 6:
            weekends.append("R,f1f1f1,0,0.0,%s" % halfday)
        # or ends with Saturday
        if len(dates) > 0 and dates[ - 1].weekday() == 5:
            weekends.append("R,f1f1f1,0,%s,1.0" % (Decimal(1) - halfday))
        return weekends
    
    def _get_title(self, options):
        title = options.get('title', '')
        if not title and 'milestone' in options:
            title = options['milestone'].split('|')[0]
        return title
    
    def _round(self, decimal_):
        return decimal_.quantize(Decimal("0.01"), ROUND_HALF_UP)
    
    def _cast_estimate(self, estimate):
        # Treat 0, empty string or None as 0.0
        if not estimate:
            return Decimal(0)
        try:
            return Decimal(estimate)
        except (TypeError, ValueError, InvalidOperation):
            # Treat other incorrect values as None
            return None
