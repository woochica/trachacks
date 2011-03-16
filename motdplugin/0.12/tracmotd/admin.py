"""
 Created by Christian Masopust 2011
 Copyright (c) 2011 Christian Masopust. All rights reserved.
"""

import re
import os.path

from trac.core import *
from trac.web.chrome import ITemplateProvider, add_notice, add_warning
from trac.admin.web_ui import IAdminPanelProvider

class MessageOfTheDayAdmin(Component):
    """ Provides a plugin to insert a 'Message Of The Day' to each page.
    """

    implements(IAdminPanelProvider, ITemplateProvider)

    # ITemplateProvider methods:
    #
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('tracmotd', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IAdminPanelProvider methods:
    #
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield('motd', 'MessageOfTheDay', 'settings', 'Settings')

    def render_admin_panel(self, req, cat, page, component):
        req.perm.assert_permission('TRAC_ADMIN')

        data = {}
        warnings = False

        if req.method == 'POST':
            if not os.path.isfile(req.args.get('message_file')):
                add_warning(req, 'message_file ' + req.args.get('message_file') + ' does not exist!')
                warnings = True
            self.env.config.set('motd', 'message_file', req.args.get('message_file'))

            if not os.path.isdir(req.args.get('message_dir')):
                add_warning(req, 'message_dir ' + req.args.get('message_dir') + ' does not exist!')
                warnings = True
            self.env.config.set('motd', 'message_dir', req.args.get('message_dir'))

            #self.env.config.set('motd', 'date_format', req.args.get('date_format'))

            fw = req.args.get('frame_width')
            if int(fw) < 400: fw = 400
            if int(fw) > 900: fw = 900
            self.env.config.set('motd', 'frame_width', fw)

            fh = req.args.get('frame_height')
            if int(fh) < 300: fh = 300
            if int(fh) > 800: fh = 800
            self.env.config.set('motd', 'frame_height', fh)

            self.env.config.save()

            if warnings:
                add_notice(req, 'Configuration saved, with warnings')
            else:
                add_notice(req, 'Configuration saved')

        data['message_file'] = self.env.config.get('motd', 'message_file')
        data['message_dir'] = self.env.config.get('motd', 'message_dir')
        data['date_format'] = self.env.config.get('motd', 'date_format')
        data['frame_width'] = self.env.config.get('motd', 'frame_width')
        data['frame_height'] = self.env.config.get('motd', 'frame_height')

        return 'admin_motd.html', data

