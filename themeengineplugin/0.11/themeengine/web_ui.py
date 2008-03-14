# Created by Noah Kantrowitz on 2007-07-15.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.
from pkg_resources import resource_filename

from trac.core import *
from trac.core import ComponentMeta
from trac.web.chrome import ITemplateProvider, add_stylesheet, Chrome
from trac.web.api import IRequestFilter

from api import ThemeEngineSystem

class ThemeEngineModule(Component):
    """A module to provide the theme content."""

    implements(ITemplateProvider, IRequestFilter)

    def __init__(self):
        # Force us to the front so we can override other templates
        ComponentMeta._registry[ITemplateProvider].remove(ThemeEngineModule)
        ComponentMeta._registry[ITemplateProvider].insert(0, ThemeEngineModule)
        
        self.system = ThemeEngineSystem(self.env)
        self._last_theme = self.system.theme
        
    def theme(self):
        cur_theme = self.system.theme
        if cur_theme is not self._last_theme:
            # We have changed themes, reset the template loader
            self.log.debug('ThemeEngine: Changing theme from %s to %s', 
                           (self._last_theme and self._last_theme['name'] or 'default'),
                           (cur_theme and cur_theme['name'] or 'default'))
            Chrome(self.env).templates = None
            self._last_theme = cur_theme
        return cur_theme
    theme = property(theme)

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        theme = self.theme
        if theme and 'htdocs' in theme:
            yield 'theme', resource_filename(theme['module'], theme['htdocs'])
            
    def get_templates_dirs(self):
        theme = self.theme
        if theme and 'templates' in theme:
            yield resource_filename(theme['module'], theme['templates'])
        
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
            
    def post_process_request(self, req, template, data, content_type):
        theme = self.theme
        if theme and 'css' in theme:
            add_stylesheet(req, 'theme/'+theme['css'])
        return template, data, content_type