# Created by Noah Kantrowitz on 2007-08-05.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.
from pkg_resources import resource_filename, resource_string

from trac.core import *
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.web.api import IRequestHandler, HTTPNotFound
from trac.perm import IPermissionRequestor
from trac.admin.api import IAdminPanelProvider

from themeengine.api import ThemeEngineSystem

class ThemeAdminModule(Component):
    """An admin panel for ThemeEngine."""

    implements(IAdminPanelProvider, IPermissionRequestor, ITemplateProvider, IRequestHandler)
    
    def __init__(self):
        self.system = ThemeEngineSystem(self.env)

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('THEME_ADMIN'):
            yield 'theme', 'Theme', 'simple', 'Simple'
            yield 'theme', 'Theme', 'advanced', 'Advanced'

    def render_admin_panel(self, req, cat, page, path_info):
        if req.method == 'POST':
            self.config.set('theme', 'theme', req.args['theme'])
            self.config.save()
            
            req.redirect(req.href.admin(cat, page)) 
        
        data = {
            'themeengine': {
                'info': self.system.info,
            },
        }
        
        theme_name = self.system.theme_name or 'default'
        data['themeengine']['current'] = theme_name
        index = 0
        for i, (k, _) in enumerate(self.system.info.iteritems()):
            if k == theme_name:
                index = i
                break
        data['themeengine']['current_index'] = index+1
        
        add_stylesheet(req, 'themeengine/jquery.jcarousel.css')
        add_stylesheet(req, 'themeengine/skins/tango/skin.css')
        add_script(req, 'themeengine/jquery.jcarousel.pack.js')
        return 'admin_theme.html', data
        
    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'THEME_ADMIN'
        
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        yield 'themeengine', resource_filename(__name__, 'htdocs')
            
    def get_templates_dirs(self):
        yield resource_filename(__name__, 'templates')
        
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/themeengine')

    def process_request(self, req):
        data = {}
        
        path_info = req.path_info[13:]
        if path_info.startswith('screenshot/'):
            return self._send_screenshot(req, data, path_info[11:])
            
        raise TracError
        
    def _send_screenshot(self, req, data, name):
        if name not in self.system.info:
            raise HTTPNotFound('Invalid theme name "%s"', name)
        theme = self.system.info[name]
        
        if 'screenshot' in theme:
            img = resource_string(theme['module'], theme['screenshot'])
        else:
            img = resource_string(__name__, 'htdocs/no_screenshot.png')
        req.send(img, 'image/png')