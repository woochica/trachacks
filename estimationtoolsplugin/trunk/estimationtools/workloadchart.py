from datetime import timedelta
from estimationtools.utils import *
from trac.util.html import Markup
from trac.wiki.macros import WikiMacroBase
import copy

DEFAULT_OPTIONS = {'width': '400', 'height': '100', 'color': 'ff9900'}

class WorkloadChart(WikiMacroBase):
    """Creates workload chart for given milestone.

    This macro creates a pie chart that shows the remaining estimated workload per ticket owner,
    and the remaining work days.
    It has the following parameters:
     * `milestone`: '''mandatory''' parameter that specifies the milestone. 
     * `width`: width of resulting diagram (defaults to 400)
     * `height`: height of resulting diagram (defaults to 100)
     * `color`: color specified as 6-letter string of hexadecimal values in the format `RRGGBB`.
       Defaults to `ff9900`, a nice orange.
     
    Examples:
    {{{
        [[WorkloadChart(milestone = Sprint 1)]]
        [[WorkloadChart(milestone = Sprint 1, width = 600, height = 100, color = 00ff00)]]
    }}}
    """

    estimation_field = get_estimation_field()
    
    def render_macro(self, req, name, content):
        if not (req.perm.has_permission('TICKET_VIEW') or 
                req.perm.has_permission('TICKET_VIEW_CC')):
            raise TracError('TICKET_VIEW or TICKET_VIEW_CC permission required')
        options = copy.copy(DEFAULT_OPTIONS)
        if content:
            for arg in content.split(','):
                i = arg.index('=')
                options[arg[:i].strip()] = arg[i+1:].strip()
        db = self.env.get_db_cnx()
        options = parse_options(db, options)
        milestone = options['milestone']
        cursor = db.cursor()
        cursor.execute("SELECT owner, p.value "
                       "  FROM ticket t, ticket_custom p"
                       "  WHERE p.ticket = t.id and p.name = %s"
                       "  AND t.milestone = %s", [self.estimation_field, milestone])
        sum = 0.0
        estimations = {}
        for owner, estimation in cursor:
            try:
                sum += float(estimation)
                if estimations.has_key(owner):
                    estimations[owner] += float(estimation)
                else:
                    estimations[owner] = float(estimation)
            except:
                pass

        estimations_string = []
        labels = []
        for owner, estimation in estimations.iteritems():
            labels.append("%s %sh" % (owner, str(int(estimation))))
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
            title += ' %sh (%s workdays left)' % (int(sum), days_remaining)
                
                
        return Markup("<img src=\"http://chart.apis.google.com/chart?"
               "chs=%sx%s" 
               "&amp;chd=t:%s"
               "&amp;cht=p3"
               "&amp;chtt=%s"
               "&amp;chl=%s"
               "&amp;chco=%s\" "
               "alt=\'Workload Chart\' />" 
               % (options['width'], options['height'], ",".join(estimations_string), 
                  title, "|".join(labels), options['color']))
