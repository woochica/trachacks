#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.admin import IAdminPanelProvider
from trac.core import implements
from trac.perm import IPermissionRequestor

from crypto.api import _, dgettext
from crypto.web_ui import CommonTemplateProvider


class CryptoAdminPanel(CommonTemplateProvider):
    """Admin panel for easier setup and configuration changes."""

    implements(IAdminPanelProvider, IPermissionRequestor)

    # IPermissionRequestor method
    def get_permission_actions(self):
        actions = ['CRYPTO_ADMIN']
        return actions

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if req.perm.has_permission('CRYPTO_ADMIN'):
            yield ('crypto', _('Cryptography'), 'config', _('Configuration'))

    def render_admin_panel(self, req, cat, page, path_info):
        # Get current configuration.
        if req.method == 'POST':
            # Save configuration changes.
            test = 'replace_with_real_code'
        # Display current configuration.
        data = {'_dgettext': dgettext}
        return 'admin_crypto.html', data
