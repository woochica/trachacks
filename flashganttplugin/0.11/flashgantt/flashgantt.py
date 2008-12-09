# Copyright 2008 Andrew De Ponte, Patrick Murphy
#
# This file is part of FlashGanttPlugin
#
# FlashGanttPlugin is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# FlashGanttPlugin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FlashGanttPlugin. If not, see <http://www.gnu.org/licenses/>.

from genshi.builder import tag

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.ticket import Milestone

import datetime

from trac.util.datefmt import format_date

class FlashGanttPlugin(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'flashgantt'
    def get_navigation_items(self, req):
        yield ('mainnav', 'flashgantt',
            tag.a('Flash Gantt', href=req.href.flashgantt()))

    # IRequestHandler methods
    def match_request(self, req):
        if (req.path_info == '/flashgantt' or req.path_info == '/flashgantt/chartxml'):
            return True
        else:
            return False
    def process_request(self, req):
        if req.path_info == '/flashgantt/chartxml':
            req.perm.require('MILESTONE_VIEW')
        
            showall = req.args.get('show') == 'all'

            # Get the current date and time
            cur_dt = datetime.date.today()

            # Get the quarter I am in.
            cur_quarter = self._get_quarter(cur_dt.month)
            prev_quarter = self._get_prev_quarter(cur_quarter)
            next_quarter = self._get_next_quarter(cur_quarter)

            (cq_sd, cq_ed) = self._get_quarter_start_end_dates(cur_dt.year, cur_quarter)
            (pq_sd, pq_ed) = self._get_prev_quarters_start_end_dates(cur_dt.year, cur_quarter)
            (nq_sd, nq_ed) = self._get_next_quarters_start_end_dates(cur_dt.year, cur_quarter)
            min_date = pq_sd.strftime('%d/%m/%Y')
            max_date = nq_ed.strftime('%d/%m/%Y')

            quarters = []
            quarters.append({'name': 'Q' + str(prev_quarter) + ' ' + str(pq_sd.year), 'start_date': pq_sd.strftime('%d/%m/%Y'), 'end_date': pq_ed.strftime('%d/%m/%Y')})
            quarters.append({'name': 'Q' + str(cur_quarter) + ' ' + str(cq_sd.year), 'start_date': cq_sd.strftime('%d/%m/%Y'), 'end_date': cq_ed.strftime('%d/%m/%Y')})
            quarters.append({'name': 'Q' + str(next_quarter) + ' ' + str(nq_sd.year), 'start_date': nq_sd.strftime('%d/%m/%Y'), 'end_date': nq_ed.strftime('%d/%m/%Y')})
            
            months = []
            for x in range(pq_sd.month, (pq_ed.month + 1)):
                (cm_sd, cm_ed) = self._get_month_start_end_dates(pq_sd.year, x)
                months.append({'name': self._get_month_name(x), 'start_date': cm_sd.strftime('%d/%m/%Y'), 'end_date': cm_ed.strftime('%d/%m/%Y')})
            for x in range(cq_sd.month, (cq_ed.month + 1)):
                (cm_sd, cm_ed) = self._get_month_start_end_dates(cq_sd.year, x)
                months.append({'name': self._get_month_name(x), 'start_date': cm_sd.strftime('%d/%m/%Y'), 'end_date': cm_ed.strftime('%d/%m/%Y')})
            for x in range(nq_sd.month, (nq_ed.month + 1)):
                (cm_sd, cm_ed) = self._get_month_start_end_dates(nq_sd.year, x)
                months.append({'name': self._get_month_name(x), 'start_date': cm_sd.strftime('%d/%m/%Y'), 'end_date': cm_ed.strftime('%d/%m/%Y')})

            milestones = []
            db = self.env.get_db_cnx()
            ms = [m for m in Milestone.select(self.env, showall, db)
                  if 'MILESTONE_VIEW' in req.perm(m.resource)]
            cnt = 0
            for m in ms:
                cnt = cnt + 1
                comp_stat = 0
                if (m.is_completed):
                    comp_stat = 1
                milestones.append({'name': m.name, 'id': str(cnt),
                'start_date': pq_sd.strftime('%d/%m/%Y'),
                'due_date': format_date(m.due, format='%d/%m/%Y'),
                'completed_date': format_date(m.completed, format='%d/%m/%Y'),
                'completed': comp_stat})
            data = {'milestones': milestones, 'showall': showall, 'visible_months': months, 'quarters': quarters}
                
            # This tuple is for Genshi (template_name, data, content_type)
            # Without data the trac layout will not appear.
            return ('chart.xml', data, 'text/xml')
        else:
            
            req.perm.require('MILESTONE_VIEW')
        
            showall = req.args.get('show') == 'all'

            db = self.env.get_db_cnx()
            milestones = [m for m in Milestone.select(self.env, showall, db)
                          if 'MILESTONE_VIEW' in req.perm(m.resource)]

            chart_height = 150 + (len(milestones) * 29)
            if (showall):
                xmlcharturl = req.href.flashgantt('/chartxml?show=all')
            else:
                xmlcharturl = req.href.flashgantt('/chartxml')

            data = {'milestones': milestones, 'showall': showall,
            'xmlcharturl': xmlcharturl, 'chart_height': chart_height}
        
            #add_stylesheet(req, 'fg/css/flashgantt.css')
        
            # This tuple is for Genshi (template_name, data, content_type)
            # Without data the trac layout will not appear.
            return ('flashgantt.html', data, None)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('fg', resource_filename(__name__, 'htdocs'))]

    def _get_month_start_end_dates(self, year, month):
        thirtyone_months = [1, 3, 5, 7, 8, 10, 12]
        thirty_months = [4, 6, 9, 11]

        start_date = None
        end_date = None
        if (month in thirty_months):
            start_date = datetime.date(year, month, 1)
            end_date = datetime.date(year, month, 30)
        elif (month in thirtyone_months):
            start_date = datetime.date(year, month, 1)
            end_date = datetime.date(year, month, 31)
        elif (month == 2):
            if (year % 4) == 0: # leap year hence, has 29 days
                start_date = datetime.date(year, month, 1)
                end_date = datetime.date(year, month, 29)
            else: # has 28 days
                start_date = datetime.date(year, month, 1)
                end_date = datetime.date(year, month, 28)

        return (start_date, end_date)

    def _get_month_name(self, month):
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return month_names[(month - 1)]

    def _get_quarter(self, month):
        quarters = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]

        quarter_its_in = None
        for x in range(0, 4):
            if (month in quarters[x]):
                quarter_its_in = (x + 1)
                break;

        return quarter_its_in
    
    def _get_quarter_start_end_months(self, quarter):
        quarters = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
        return (quarters[quarter - 1][0], quarters[quarter - 1][2])

    def _get_quarter_start_end_dates(self, year, quarter):
        (qstart_month, qend_month) = self._get_quarter_start_end_months(quarter)
        (qstart_date, _) = self._get_month_start_end_dates(year, qstart_month)
        (_, qend_date) = self._get_month_start_end_dates(year, qend_month)

        return (qstart_date, qend_date)

    def _get_prev_quarters_start_end_dates(self, year, quarter):
        if (quarter == 1):
            # subtract one from the year and use the 4 quarter of that
            # year
            return self._get_quarter_start_end_dates((year - 1), 4)
        else:
            # use the provided year and subtract one from the provided
            # quarter
            return self._get_quarter_start_end_dates(year, (quarter - 1))

    def _get_next_quarters_start_end_dates(self, year, quarter):
        if (quarter == 4):
            # add one to the year and use the 1 quarter of that year
            return self._get_quarter_start_end_dates((year + 1), 1)
        else:
            # use the provided year and add one to the provided quarter
            return self._get_quarter_start_end_dates(year, (quarter + 1))

    def _get_prev_quarter(self, quarter):
        if (quarter == 1):
            return 4
        else:
            return quarter - 1

    def _get_next_quarter(self, quarter):
        if (quarter == 4):
            return 1
        else:
            return quarter + 1
