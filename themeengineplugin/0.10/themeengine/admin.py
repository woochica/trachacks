# -*- coding: utf-8 -*-
#
# Copyright (c) 2006-2010 Noah Kantrowitz <noah@coderanger.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.core import *
from trac.perm import IPermissionRequestor
from trac.web.chrome import add_script

from webadmin.web_ui import IAdminPageProvider

from filter import ThemeFilterModule

__all__ = ['ThemeAdminModule']

class ThemeAdminModule(Component):
    """An admin panel for ThemeEngine."""

    implements(IAdminPageProvider, IPermissionRequestor)
    
    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('THEME_ADMIN'):
            yield 'general', 'General', 'theme', 'Theme'
            
    def process_admin_request(self, req, cat, page, path_info):
        filter = ThemeFilterModule(self.env)
        info = filter.info.items()
        theme_name = filter.theme_name
        index = 0
        for i, (k, _) in enumerate(info):
            if k == theme_name:
                index = i
                break
                
        if req.method == 'POST':
            theme = req.args.get('theme', '')
            self.config.set('theme', 'theme', theme)
            self.config.save()
            req.redirect(req.href.admin(cat, page))
        
        for k,v in info:
            req.hdf['themeengine.info.'+k] = v
        req.hdf['themeengine.current'] = theme_name
        req.hdf['themeengine.current_index'] = index+1
        req.hdf['themeengine.href'] = req.href.admin(cat, page)
        req.hdf['themeengine.href.htdocs'] = req.href.chrome('themeengine')
        req.hdf['themeengine.href.screenshot'] = req.href.themeengine('screenshot')
        
        add_script(req, 'themeengine/jquery.js')
        add_script(req, 'themeengine/jcarousel.js')
        return 'admin_themeengine.cs', None
        
    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'THEME_ADMIN'
