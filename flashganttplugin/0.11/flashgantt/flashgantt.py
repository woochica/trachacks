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

            quarters = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]

            # Get the current date and time
            cur_dt = datetime.today()

            # Figure out what month the cur_dt is in.
            cur_month = cur_dt.month

            # Figure out what Quarter the cur_dt is in.
            cur_quarter = None
            for quarter_index in range(0,4):
                if cur_month in quarters[quarter_index]:
                    cur_quarter = quarter_index
                    break;

            # Figure out the beginnig of tha Quarter it is in.
            calendar

            # Calculate the beginning date of the Quarter before that
            # one.
            prev_quarter = None
            if (cur_quarter == 0):
                prev_quarter = 4
            else:
                prev_quarter = cur_quarter - 1

            # Calculate the ending date of the Quarter after that
            # one.
            next_quarter = None
            if (cur_quarter == 4):
                next_quarter = 1
            else:
                next_quarter = cur_quarter + 1

            db = self.env.get_db_cnx()
            #milestones = [m for m in Milestone.select(self.env, showall, db)
            #              if 'MILESTONE_VIEW' in req.perm(m.resource)]
            months = [{'name':'March', 'start_date':'1/3/2005', 'end_date':'31/3/2005'},
                      {'name':'April', 'start_date':'1/4/2005', 'end_date':'30/4/2005'},
                      {'name':'May', 'start_date':'1/5/2005', 'end_date':'31/5/2005'},
                      {'name':'June', 'start_date':'1/6/2005', 'end_date':'30/6/2005'},
                      {'name':'July', 'start_date':'1/7/2005', 'end_date':'31/7/2005'},
                      {'name':'August', 'start_date':'1/8/2005', 'end_date':'31/8/2005'}]
            milestones = [{'name':'writing', 'index':'1', 'start_date':'7/3/2005', 'due_date':'18/4/2005', 'completed_date':'22/4/2005'},
                          {'name':'signing', 'index':'2', 'start_date':'6/4/2005', 'due_date':'2/5/2005', 'completed_date':'12/5/2005'},
                          {'name':'financing', 'index':'3', 'start_date':'1/5/2005', 'due_date':'2/6/2005', 'completed_date':'2/6/2005'},
                          {'name':'permission', 'index':'4', 'start_date':'13/5/2005', 'due_date':'12/6/2005', 'completed_date':'19/6/2005'},
                          {'name':'plumbing', 'index':'5', 'start_date':'2/5/2005', 'due_date':'12/6/2005', 'completed_date':'19/6/2005'}]
            data = {'milestones': milestones, 'showall': showall, 'visible_months':months, 'min_date':'1/3/2005', 'max_date':'31/8/2005'}
                
            # This tuple is for Genshi (template_name, data, content_type)
            # Without data the trac layout will not appear.
            return ('chart.xml', data, 'text/xml')
        else:
            
            req.perm.require('MILESTONE_VIEW')
        
            showall = req.args.get('show') == 'all'

            db = self.env.get_db_cnx()
            milestones = [m for m in Milestone.select(self.env, showall, db)
                          if 'MILESTONE_VIEW' in req.perm(m.resource)]

            data = {'milestones': milestones, 'showall': showall}
        
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
            end_date = datetime.date(year, month, 31)
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
    
    def _get_quarter(self, month):
        quarters = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]

        quarter_its_in = None
        for x in range(0, 4):
            if (quarter in quarters[x]):
                quarter_its_in = x
                break;

        return quarter_its_in
    
    def _get_quarter_start_end_months(self, quarter):
        quarters = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
        return (quarters[quarter][0], quarters[quarter][3])

    def _get_quarter_start_end_dates(self, year, quarter):
        (qstart_month, qend_month) = _get_quarter_start_end_months(quarter)
        (qstart_date, _) = self._get_month_start_end_dates(year, qstart_month)
        (_, qend_date) = self._get_month_start_end_dates(year, qend_month)

        return (qstart_date, qend_date)

    def _get_prev_quarters_start_end_dates(self, year, quarter):
        if (quarter == 1):
            # subtract one from the year and use the 4 quarter of that
            # year
            return _get_quarter_start_end_dates((year - 1), 4)
        else:
            # use the provided year and subtract one from the provided
            # quarter
            return _get_quarter_start_end_dates(year, (quarter - 1))

    def _get_next_quarters_start_end_dates(self, year, quarter):
        if (quarter == 4):
            # add one to the year and use the 1 quarter of that year
            return _get_quarter_start_end_dates((year + 1), 1)
        else:
            # use the provided year and add one to the provided quarter
            return _get_quarter_start_end_dates(year, (quarter + 1))
