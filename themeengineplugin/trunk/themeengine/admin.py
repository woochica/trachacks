# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2010 Noah Kantrowitz <noah@coderanger.net>
# Copyright (c) 2013      Olemis Lang <olemis+trac@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import os.path

from pkg_resources import resource_filename, resource_string

from trac.core import *
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.web.api import IRequestHandler, HTTPNotFound
from trac.perm import IPermissionRequestor
from trac.admin.api import IAdminPanelProvider

from themeengine.api import ThemeEngineSystem, ThemeNotFound

class SimpleThemeAdminModule(Component):
    """An admin panel for ThemeEngine."""

    implements(IAdminPanelProvider, IPermissionRequestor, ITemplateProvider, IRequestHandler)
    
    def __init__(self):
        self.system = ThemeEngineSystem(self.env)

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('THEME_ADMIN'):
            yield 'theme', 'Theme', 'theme', 'Theme'

    def render_admin_panel(self, req, cat, page, path_info):
        if req.method == 'POST':
            self.config.set('theme', 'theme', req.args['theme'].lower())
            self.config.save()
            
            req.redirect(req.href.admin(cat, page)) 
        
        data = {
            'themeengine': {
                'info': self.system.info.items(),
            },
        }

        try:
            theme_name = self.system.theme and self.system.theme['name'] \
                                           or 'default'
        except ThemeNotFound:
            theme_name = 'default'
        theme_name = theme_name.islower() and theme_name.title() or theme_name
        data['themeengine']['current'] = theme_name
        index = 0
        curtheme = None
        for i, (k, v) in enumerate(data['themeengine']['info']):
            if k.lower() == theme_name.lower():
                index = i
                curtheme = v
                break
        data['themeengine']['current_index'] = index
        data['themeengine']['current_theme'] = curtheme
            
        #add_stylesheet(req, 'themeengine/jquery.jcarousel.css')
        #add_stylesheet(req, 'themeengine/skins/tango/skin.css')
        #add_script(req, 'themeengine/jquery.jcarousel.pack.js')
        add_stylesheet(req, 'themeengine/admin.css')
        add_script(req, 'themeengine/jcarousellite_1.0.1.js')
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
        elif path_info == 'theme.css':
            req.send_file(os.path.join(self.env.path, 'htdocs', 'theme.css'), 'text/css')
        
        raise HTTPNotFound("The requested URL was not found on this server")
    
    def _send_screenshot(self, req, data, name):
        if name not in self.system.info:
            raise HTTPNotFound("Invalid theme name '%s'", name)
        theme = self.system.info[name]
        
        if 'screenshot' in theme:
            img = resource_string(theme['module'], theme['screenshot'])
        else:
            img = resource_string(__name__, 'htdocs/no_screenshot.png')
        req.send(img, 'image/png')


class CustomThemeAdminModule(Component):
    """An admin panel for ThemeEngine."""

    implements(IAdminPanelProvider)

    def __init__(self):
        self.system = ThemeEngineSystem(self.env)

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('THEME_ADMIN'):
            yield 'theme', 'Theme', 'custom', 'Customize'
            yield 'theme', 'Theme', 'advanced', 'Customize: Advanced'

    def render_admin_panel(self, req, cat, page, path_info):
        data = {
            'themes': self.system.info.items(),
        }
        
        theme_name = self.system.theme_name or 'Default'
        data['current'] = theme_name
        index = 0
        curtheme = None
        for i, (k, v) in enumerate(data['themes']):
            if k == theme_name:
                index = i
                curtheme = v
                break
        data['current_index'] = index
        data['current_theme'] = curtheme
        
        colors = {}
        if curtheme:
            for name, prop, selector in curtheme.get('colors', ()):
                # Check the config first
                val = self.config.get('theme', 'color.'+name)
                if not val and curtheme.get('schemes'):
                    # Then look for a scheme
                    val = curtheme['schemes'][0][1].get(name)
                if not val:
                    # Otherwise use black for foreground and white for background
                    if prop == 'color':
                        val = '#000000'
                    else:
                        val = '#ffffff'
                colors[name] = val
        data['colors'] = colors
        data['enable'] = self.config.getbool('theme', 'enable_css', False)
        if page == 'advanced' and os.path.exists(os.path.join(self.env.path, 'htdocs', 'theme.css')):
            data['css'] = open(os.path.join(self.env.path, 'htdocs', 'theme.css')).read()
        
        if req.method == 'POST':
            if 'enable_css' in req.args:
                self.config.set('theme', 'enable_css', 'enabled')
            else:
                self.config.set('theme', 'enable_css', 'disabled')
            
            for key, value in self.config.options('theme'):
                if key.startswith('color.'):
                    self.config.remove('theme', key)
            
            for name, color in colors.iteritems():
                color = req.args.get('color_'+name, color)
                self.config.set('theme', 'color.'+name, color)
            
            f = open(os.path.join(self.env.path, 'htdocs', 'theme.css'), 'w')
            if page == 'advanced':
                f.write(req.args.get('css', ''))
            else:
                f.write('/* Warning: this file is auto-generated. If you edit it, changes will be lost the next time you use the simple customizer. */\n')
                for name, prop, selector in curtheme.get('colors', ()):
                    color = req.args.get('color_'+name, colors.get(name, '#ffffff'))
                    f.write('%s {\n'%selector)
                    f.write('  %s: %s;\n'%(prop, color))
                    f.write('}\n\n')
            f.close()
            
            self.config.save()
            req.redirect(req.href.admin(cat, page)) 
        
        add_stylesheet(req, 'themeengine/farbtastic/farbtastic.css')
        add_stylesheet(req, 'themeengine/admin.css')
        add_script(req, 'themeengine/farbtastic/farbtastic.js')
        add_script(req, 'themeengine/jquery.rule.js')
        if page == 'advanced':
            return 'admin_theme_advanced.html', data
        else:
            return 'admin_theme_custom.html', data


