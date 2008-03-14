# Created by Noah Kantrowitz on 2007-07-15.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.
import os.path

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
        self.system = ThemeEngineSystem(self.env)

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        theme = self.system.theme
        if theme and 'htdocs' in theme:
            yield 'theme', resource_filename(theme['module'], theme['htdocs'])

    def get_templates_dirs(self):
        theme = self.system.theme
        if theme and 'template' in theme:
            yield resource_filename(theme['module'], os.path.dirname(theme['template']))

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        theme = self.system.theme
        if theme and 'css' in theme:
            add_stylesheet(req, 'theme/'+theme['css'])
        if theme and 'template' in theme:
            req.chrome['theme'] = os.path.basename(theme['template'])
        return template, data, content_type