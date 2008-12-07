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
        return req.path_info == '/flashgantt'
    def process_request(self, req):
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
