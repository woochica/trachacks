#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import os

from trac.config import BoolOption, IntOption, Option
from trac.core import implements

from crypto.api import Credential, GenericFactory, ICipherModule, _


class OpenPgpFactory(GenericFactory):
    """Provides OpenPGP functionality based on GnuPG."""

    implements(ICipherModule)

    gpg_binary = Option('crypto', 'gpg_binary', 'gpg',
        """GnuPG binary name, allows for full path too.

        Value 'gpg' is same default as in python-gnupg itself.
        For usual installations location of the gpg binary is auto-detected.
        """)
    gpg_home = Option('crypto', 'gpg_home', '.gpg',
        """Directory containing keyring files.

        In case of wrong configuration missing keyring files without content
        will be created in the configured location, provided necessary
        write permssion is granted for the corresponding parent directory.
        """)
    priv_key = Option('crypto', 'gpg_private_key', '',
        """Key ID of private key (last 8 chars or more).

        If unset, a private key will be selected from keyring automagicly.
        The password must be available i.e. provided by running gpg-agent
        (not yet available) or empty (security trade-off). No private key
        operation can happen before the key has been unlocked successfully.
        """)

    name = 'openpgp'
    _supported_keys = ['name_real', 'name_comment', 'name_email',
                       'key_type',  'key_length',
                       'subkey_type', 'subkey_length',
                       'expire_date', 'passphrase']

    def __init__(self):
        try:
            from gnupg import GPG
        except ImportError:
            raise TracError(_("""Unable to load the python-gnupg module.
                              Please check and correct your installation."""))
        try:
            # Initialize the GnuPG instance.
            path = os.path.join(os.path.abspath(self.env.path), self.gpg_home)
            self.env.log.debug('Using GnuPG home dir: ' + str(path))
            self.gpg = GPG(gpgbinary=self.gpg_binary, gnupghome=path)
        except ValueError:
            raise TracError(_("""Missing the crypto binary. Please check and
                              set full path with option 'gpg_binary'."""))

    # IKeyVault methods

    def keys(self, private=False, id_only=False):
        """Returns the list of all available keys."""
        # DEVEL: Cache this for performance.
        if not id_only:
            return self.gpg.list_keys(private) # same as gpg.list_keys(False)
        keys = []
        for key in self.gpg.list_keys(private):
            keys.append(key['fingerprint'])
        return keys

    def create_key(self, **kwargs):
        """Generate a new OpenPGP key pair."""
        # Sanitize input.
        for k in kwargs.keys():
            if k not in self._supported_keys:
                kwargs.pop(k)
        input_data = self.gpg.gen_key_input(**kwargs)
        try:
            return self.gpg.gen_key(input_data)
        except ValueError, e:
            return False, e

    def delete_key(self, key_id, perm):
        """Delete the key specified by ID."""
        perm.require('CRYPTO_DELETE')
        result = str(self.gpg.delete_keys(key_id))
        if result == 'ok':
            return True
        elif result.endswith('secret key first'):
            self.gpg.delete_keys(key_id, True)
            return str(self.gpg.delete_keys(key_id)) == 'ok'
        elif result.startswith('No such'):
            return None
        return False

    # ICipherModule methods

    def crypt_sign(self, clear, key_id, action=['sign'], password=None):
        pass

    def decrypt_verify(self, code, detached_signature=None, password=None):
        pass


class OpenPgpKey(Credential):
    """Represents a single OpenPGP key."""

    allow_usermod = BoolOption('crypto', 'gpg_keygen_allow_usermod', 'True',
                         """Allow users to overwrite key generation presets.
                         """)
    expire_date = Option('crypto', 'gpg_keygen_expire_date', '0',
                         """Expiration date, set by ISO date, number of
                         days/weeks/months/years like 365d/50w/12m/1y or an
                         epoch value like seconds=<epoch>. Zero means
                         non-expiring keys.""")
    key_type = Option('crypto', 'gpg_keygen_key_type', 'RSA',
                      """Key type, one of 'RSA' (default), 'DSA'.""")
    key_length = IntOption('crypto', 'gpg_keygen_key_length', 2048,
                           """Key bit length, supports 1024 or 2048.""")
    subkey_type = Option('crypto', 'gpg_keygen_subkey_type', 'ELG-E',
                         """Subkey type, if using DSA primary key, one of
                         'RSA', 'ELG-E'.""")
    subkey_length = IntOption('crypto', 'gpg_keygen_subkey_length', 2048,
                              """Subkey bit length, supports 1024 or 2048.""")

    factory = 'openpgp'

    def __init_(self, key_id=None, **kwargs):
        cb = CryptoBase(self.env)
        if key_id:
            key = cb.get_key(key_id)
            self.id = key['keyid']
            self.props = {
                'uid': key.get('uids')[1],
                'length': key.get('length'),
                'created': key.get('date'),
                'expires': key.get('expires'),
            }
        else:
            if properties:
                key = cb.create_key(factory, **kwargs)
