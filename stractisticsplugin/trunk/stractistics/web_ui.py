# -*- coding: utf-8 -*-
#
# Stractistics
# Copyright (C) 2008 GMV SGI Team <http://www.gmv-sgi.es>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 2 of the GNU General Public
# License as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
#
# $Id: web_ui.py 432 2008-07-11 12:58:49Z ddgb $
#

from genshi.builder import tag
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.web.api import IRequestHandler
from trac.web.chrome import (
    INavigationContributor, ITemplateProvider,
    add_ctxtnav, add_script, add_stylesheet
)

try:
    import json
except ImportError:
    import simplejson as json

from util import read_config_options
from global_reports import global_reports
from user_reports import user_reports

class StractisticsModule(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider,
               IPermissionRequestor)
    
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'stractistics'

    def get_navigation_items(self, req):
        if req.perm.has_permission('STRACTISTICS_VIEW'):
            yield 'mainnav', 'stractistics', tag.a('Stractistics',
                                                   href=req.href.stractistics())

    #IPermissionRequestor methods
    def get_permission_actions(self):
        return ['STRACTISTICS_VIEW']

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('hw', resource_filename(__name__, 'htdocs'))]

    # IRequestHandler methods
    def match_request(self, req):
        import re
        match = re.match('/stractistics(?:/([^/]+))?(?:/(.*)$)?', req.path_info)
        if match: 
            req.args['module'] = match.group(1)
            req.args['arguments'] = match.group(2)
            return True
        else:
            return False

    def process_request(self, req):
        req.perm.assert_permission('STRACTISTICS_VIEW')
        add_stylesheet(req, 'hw/css/stractistics.css')
        add_script(req, 'hw/javascript/swfobject.js')
        add_script(req, 'hw/javascript/prototype.js')
        add_script(req, 'hw/javascript/js-ofc-library/ofc.js')
        add_script(req, 'hw/javascript/js-ofc-library/data.js')
        add_script(req, 'hw/javascript/js-ofc-library/charts/area.js')
        add_script(req, 'hw/javascript/js-ofc-library/charts/bar.js')
        add_script(req, 'hw/javascript/js-ofc-library/charts/line.js')
        add_script(req, 'hw/javascript/js-ofc-library/charts/pie.js')
        add_script(req, 'hw/javascript/chart_reports.js')

        add_ctxtnav(req, 'Project Reports', req.href.stractistics("/project_reports"))
        add_ctxtnav(req, 'User Reports', req.href.stractistics("/user_reports"))

        #Reading options from trac.ini
        config = read_config_options(self.env.config)

        db = self.env.get_db_cnx()
        module = req.args.get('module', None)
        if module is not None and module == 'user_reports':
            template, data = user_reports(req, config, db)
        else:
            template, data = global_reports(req, config, db)
        data['json'] = {
            'repository_activity': json.dumps(data['repository_activity'].get_data()),
            'ticket_activity': json.dumps(data['ticket_activity'].get_data()),
            'wiki_activity': json.dumps(data['wiki_activity'].get_data()),
        }
        return template, data, None
