# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Jiang Xin <worldhello.net@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
#
# Author: Jiang Xin <worldhello.net@gmail.com>

import random

class PyCoSign(object):
    """A class for working with a CoSign server."""

    def __init__(self, url, **kwords):
        self.url = url
        self.paths = {
            'server': 'https://weblogin.localdomain',
            'service': '',
            'login_path': '/cgi-bin/login',
            'logout_path': '/cgi-bin/login',
        }
        self.paths.update(kwords)
        if self.paths['service'] and not self.paths['service'].startswith('cosign-'):
            self.paths['service'] = "cosign-" + self.paths['service']

    def random_hash(self, bytes=32):
        sample_string = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        hash = '';
        for i in range(bytes):
            hash += random.choice(sample_string)
        return hash

    def do_login(self, req):
        """Return the login URL for the given service."""
        back_url= req.abs_href.login()
        service = self.paths['service'].encode('utf-8')
        hash = self.random_hash(125)
        dest_url = self.paths['server'].rstrip('/')
        dest_url += self.paths['login_path']
        dest_url += '?' + self.paths['service'] + "=" + hash
        dest_url += ';&' + back_url
        req.outcookie[service] = hash
        req.outcookie[service]['path'] = '/'
        req.redirect(dest_url)

    def do_logout(self, req):
        """Return the logout URL."""
        back_url= req.abs_href()
        dest_url = self.paths['server'].rstrip('/')
        dest_url += self.paths['logout_path']
        dest_url += '?' + back_url
        service = self.paths['service'].encode('utf-8') or req.environ['COSIGN_SERVICE']
        if service:
            req.outcookie[service] = ""
            req.outcookie[service]['path'] = '/'
            req.outcookie[service]['expires'] = -10000
        req.redirect(dest_url)
