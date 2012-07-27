#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.prefs.api import IPreferencePanelProvider
from trac.web.chrome import ITemplateProvider, add_notice

from crypto.api import _, dgettext


class CommonTemplateProvider(Component):
    """Generic template provider."""

    implements(ITemplateProvider)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        return [resource_filename('crypto', 'templates')]

class UserCryptoPreferences(CommonTemplateProvider):
    """Provides related user preferences."""

    implements(IPreferencePanelProvider)

    # IPreferencePanelProvider methods

    def get_preference_panels(self, req):
        yield ('crypto', _('Cryptography'))

    def render_preference_panel(self, req, panel):
        if req.method == 'POST':
            new_content = req.args.get('replace_with_real_argname')
            if new_content:
                #req.session['replace_with_real_argname'] = new_content
                add_notice(req, _('Your content has been saved.'))
            req.redirect(req.href.prefs(panel or None))
        data = {
            '_dgettext': dgettext
            # content = req.session.get('replace_with_real_argname',
            #                           'your text')
        }
        return 'prefs_crypto.html', data
