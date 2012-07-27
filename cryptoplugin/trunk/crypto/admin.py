#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import os

from datetime import datetime

from trac.admin import IAdminPanelProvider
from trac.config import Option
from trac.core import implements
from trac.perm import IPermissionRequestor
from trac.util.datefmt import to_timestamp, utc
from trac.web.chrome import add_notice, add_stylesheet, add_warning

from crypto.api import CryptoBase, _, dgettext
from crypto.compat import exception_to_unicode
from crypto.web_ui import CommonTemplateProvider


class CryptoAdminPanel(CommonTemplateProvider):
    """Admin panel for easier setup and configuration changes."""

    implements(IAdminPanelProvider, IPermissionRequestor)

    # IPermissionRequestor method
    def get_permission_actions(self):
        action = ['CRYPTO_DELETE']
        actions = [('CRYPTO_ADMIN', action), action[0]]
        return actions

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if req.perm.has_permission('CRYPTO_ADMIN'):
            yield ('crypto', _('Cryptography'), 'config', _('Configuration'))

    def render_admin_panel(self, req, cat, page, path_info):
        if req.method == 'POST':
            defaults = self.config.defaults().get('crypto')
            ## Read admin form values.
            # GnuPG settings
            gpg_binary = req.args.get('gpg_binary')
            gpg_home = req.args.get('gpg_home')
            priv_key = req.args.get('priv_key')
            # Key generation presets
            expire_date = req.args.get('expire_date')
            key_length = req.args.get('key_length')
            key_type = req.args.get('key_type')
            subkey_length = req.args.get('subkey_length')
            subkey_type = req.args.get('subkey_type')
            # Checkbox return value requires special parsing.
            allow_usermod = bool(req.args.get('allow_usermod'))

            # Overwrite deleted values with defaults.
            if not gpg_binary and defaults:
                gpg_binary = defaults['gpg_binary']
            self.config.set('crypto', 'gpg_binary', gpg_binary)
            if not gpg_home and defaults:
                gpg_home = defaults['gpg_home']
            self.config.set('crypto', 'gpg_home', gpg_home)
            if not priv_key and defaults:
                priv_key = defaults['private_key']
            self.config.set('crypto', 'gpg_private_key', priv_key)

            self.config.set('crypto', 'gpg_keygen_allow_usermod',
                            allow_usermod)
            if not expire_date and defaults:
                expire_date = defaults['gpg_keygen_expire_date']
            self.config.set('crypto', 'gpg_keygen_expire_date', expire_date)
            if not key_length and defaults:
                key_length = defaults['gpg_keygen_key_length']
            self.config.set('crypto', 'gpg_keygen_key_length', key_length)
            if not key_type and defaults:
                key_type = defaults['gpg_keygen_key_type']
            self.config.set('crypto', 'gpg_keygen_key_type', key_type)
            if not subkey_length and defaults:
                subkey_length = defaults['gpg_keygen_subkey_length']
            self.config.set('crypto', 'gpg_keygen_subkey_length',
                            subkey_length)
            if not subkey_type and defaults:
                subkey_type = defaults['gpg_keygen_subkey_type']
            self.config.set('crypto', 'gpg_keygen_subkey_type', subkey_type)

            # Save effective new configuration.
            _save_config(self.config, req, self.log)
            req.redirect(req.href.admin(cat, page))

        # Get current configuration.
        gpg = {
            'binary': self.config.get('crypto', 'gpg_binary'),
            'home': self.config.get('crypto', 'gpg_home')
        }
        keygen = {
            'allow_usermod': self.config.getbool('crypto',
                                                 'gpg_keygen_allow_usermod'),
            'expire_date': self.config.get('crypto', 'gpg_keygen_expire_date'),
            'key_length': self.config.getint('crypto',
                                             'gpg_keygen_key_length'),
            'key_type': self.config.get('crypto', 'gpg_keygen_key_type'),
            'subkey_length': self.config.getint('crypto',
                                                'gpg_keygen_subkey_length'),
            'subkey_type': self.config.get('crypto', 'gpg_keygen_subkey_type')
        }
        now_ts = to_timestamp(datetime.now(utc))
        priv_key = self.config.get('crypto', 'gpg_private_key')
        priv_keys = [dict(id='', label=_("(Select private key)"))] + [
            dict(id=key['keyid'],
                 label=' - '.join([key['keyid'], key.get('uids')[1]]),
                 disabled=key.get('expires') and \
                          int(key.get('expires')) < now_ts,
                 selected=key['keyid'] == priv_key)
            for key in CryptoBase(self.env).keys(private=True)
        ]
            
        data = {
            '_dgettext': dgettext,
            'env_dir': os.path.abspath(self.env.path),
            'gpg': gpg,
            'keygen': keygen,
            'priv_keys': priv_keys
        }
        add_stylesheet(req, 'crypto/crypto.css')
        return 'admin_crypto.html', data


def _save_config(config, req, log):
    """Try to save the config, and display either a success notice or a
    failure warning (code copied verbatim from Trac core).
    """
    try:
        config.save()
        add_notice(req, _("Your changes have been saved."))
    except Exception, e:
        log.error('Error writing to trac.ini: %s', exception_to_unicode(e))
        add_warning(req, _("""Error writing to trac.ini, make sure it is
                           writable by the web server. Your changes have not
                           been saved."""))
