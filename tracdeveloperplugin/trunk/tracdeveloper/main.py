# -*- coding: utf-8 -*-

import re

from genshi.builder import tag
from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.prefs.api import IPreferencePanelProvider

__all__ = ['DeveloperPlugin']


class DeveloperPlugin(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider, IPreferencePanelProvider)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'developer'

    def get_navigation_items(self, req):
        yield ('metanav', 'developer',
               tag.a('Developer Tools', href=req.href.developer()))

    # IRequestHandler methods

    def match_request(self, req):
        return re.match(r'/developer/?$', req.path_info)

    def process_request(self, req):
        return 'developer/index.html', {}, None

    # ITemplateProvider methods

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('developer', resource_filename(__name__, 'htdocs'))]

    # IPreferencePanelProvider methods
    def get_preference_panels(self, req):
        yield 'developer', 'Developer Options'

    def render_preference_panel(self, req, panel):
        if req.method == 'POST':
            req.session['developer.js.enable_debug'] = req.args.get('enable_debug', '0')
        return 'developer/prefs_developer.html', {}