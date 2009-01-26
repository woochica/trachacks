from datetime import timedelta
from estimationtools.utils import parse_options, execute_query, get_estimation_field, get_estimation_suffix, get_closed_states
from trac.util.html import Markup
from trac.wiki.macros import WikiMacroBase
import copy

DEFAULT_OPTIONS = {'width': '400', 'height': '100', 'color': 'ff9900'}

class WorkloadChart(WikiMacroBase):
    """Creates workload chart for the selected tickets.

    This macro creates a pie chart that shows the remaining estimated workload per ticket owner,
    and the remaining work days.
    It has the following parameters:
     * a comma-separated list of query parameters for the ticket selection, in the form "key=value" as specified in TracQuery#QueryLanguage.
     * `width`: width of resulting diagram (defaults to 400)
     * `height`: height of resulting diagram (defaults to 100)
     * `color`: color specified as 6-letter string of hexadecimal values in the format `RRGGBB`.
       Defaults to `ff9900`, a nice orange.

    Examples:
    {{{
        [[WorkloadChart(milestone=Sprint 1)]]
        [[WorkloadChart(milestone=Sprint 1, width=600, height=100, color=00ff00)]]
    }}}
    """

    estimation_field = get_estimation_field()
    estimation_suffix = get_estimation_suffix()
    closed_states = get_closed_states()

    def render_macro(self, req, name, content):
        db = self.env.get_db_cnx()
        # prepare options
        options, query_args = parse_options(db, content, copy.copy(DEFAULT_OPTIONS))

        query_args[self.estimation_field + "!"] = None
        tickets = execute_query(self.env, req, query_args)

        sum = 0.0
        estimations = {}
        for ticket in tickets:
            if ticket['status'] in self.closed_states:
                continue
            try:
                estimation = float(ticket[self.estimation_field])
                owner = ticket['owner']
                sum += estimation
                if estimations.has_key(owner):
                    estimations[owner] += estimation
                else:
                    estimations[owner] = estimation
            except:
                pass

        estimations_string = []
        labels = []
        for owner, estimation in estimations.iteritems():
            labels.append("%s %s%s" % (owner, str(int(estimation)), self.estimation_suffix))
            estimations_string.append(str(int(estimation)))

        # Title
        title = 'Workload'

        # calculate remaining work time
        if options.get('today') and options.get('enddate'):
            currentdate = options['today']
            day = timedelta(days=1)
            days_remaining = 0
            while currentdate <= options['enddate']:
                if currentdate.weekday() < 5:
                    days_remaining += 1
                currentdate += day
            title += ' %s%s (%s workdays left)' % (int(sum), self.estimation_suffix, days_remaining)

        return Markup("<img src=\"http://chart.apis.google.com/chart?"
               "chs=%sx%s"
               "&amp;chf=bg,s,00000000"
               "&amp;chd=t:%s"
               "&amp;cht=p3"
               "&amp;chtt=%s"
               "&amp;chl=%s"
               "&amp;chco=%s\" "
               "alt=\'Workload Chart\' />"
               % (options['width'], options['height'], ",".join(estimations_string),
                  title, "|".join(labels), options['color']))
