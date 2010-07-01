# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2008 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# ==============================================================================

from trac.admin import IAdminPanelProvider
from trac.config import Option, _TRUE_VALUES
from trac.core import Component, implements
from trac.web.chrome import add_stylesheet

class GoogleAnalyticsAdmin(Component):
    config = env = log = None
    options = {}
    implements(IAdminPanelProvider)

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('google', 'Google', 'analytics', 'Analytics')

    def render_admin_panel(self, req, cat, page, path_info):
        add_stylesheet(req, 'googleanalytics/googleanalytics.css')
        if req.method.lower() == 'post':
            self.config.set('google.analytics', 'uid',
                            req.args.get('uid'))
            self.config.set('google.analytics', 'admin_logging',
                            req.args.get('admin_logging') in _TRUE_VALUES)
            self.config.set('google.analytics', 'authenticated_logging',
                            req.args.get('authenticated_logging') in
                            _TRUE_VALUES)
            self.config.set('google.analytics', 'outbound_link_tracking',
                            req.args.get('outbound_link_tracking') in \
                            _TRUE_VALUES)
            self.config.set('google.analytics', 'google_external_path',
                            req.args.get('google_external_path'))
            self.config.set('google.analytics', 'extensions',
                            req.args.get('extensions'))
            self.config.set('google.analytics', 'tracking_domain_name',
                            req.args.get('tracking_domain_name'))
            self.config.save()
        self.update_config()
        return 'google_analytics_admin.html', {'ga': self.options}

    def update_config(self):
        for option in [option for option in Option.registry.values()
                       if option.section == 'google.analytics']:
            if option.name in ('admin_logging', 'authenticated_logging',
                               'outbound_link_tracking'):
                value = self.config.getbool('google.analytics', option.name,
                                            option.default)
                option.value = value
            else:
                value = self.config.get('google.analytics', option.name,
                                        option.default)
                option.value = value
            self.options[option.name] = option
