#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 Copyright (C) 2008 General de Software de Canarias.
 Author: Carlos López Pérez <carlos.lopezperez@gmail.com>

 Copyright (C) 2009 Jiang Xin <worldhello.net@gmail.com>
   Synchronize user account information with LDAP.
 Author: Jiang Xin <worldhello.net@gmail.com>
"""

import re, ldap

from trac.core import implements, Component
from trac.web.api import IRequestFilter

class AccountLDAP(Component):
    """Gestiona el api para la interacción con el LDAP y la gestión del trac
    """
    implements(IRequestFilter)
    
    def __init__(self):
        """Se realiza la conexión con el LDAP.
        """
        self.basedn = self.config.get('ldap', 'basedn')
        self.userdn = self.config.get('ldap', 'user_rdn')
        self.attempts = 1
        if self.config.has_option('ldap', 'attempts'):
            self.attempts = self.config.getint('ldap', 'attempts')
        self.userFilter = 'uid'
        if self.config.has_option('ldap', 'user_filter'):
            self.userFilter = self.config.get('ldap', 'user_filter')
        self.enabled = True
        for i in range(self.attempts):
            try:
                self.ldap = ldap.open(self.config.get('ldap', 'host'))
                self.ldap.simple_bind_s(self.config.get('ldap', 'bind_user'),  
                                      self.config.get('ldap', 'bind_passwd'))
                break
            except ldap.LDAPError, e:
                self.enabled = False
                self.log.error('Connection LDAP problems. Check trac.ini ldap options. Attempt', (i + 1))
        self.log.info('Connection LDAP basdn %s" userdn "%s". Attempt %i' % (self.basedn, 
                                                                 self.userdn, (i + 1)))
        
    #
    #------------------------------------------------- IRequestFilter interface
    #
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if not self.enabled or not req.authname or req.authname == 'anonymous':
            return template, data, None

        # If login from CoSign SSO, redirecting from CoSign, no referer is set in header.
        # Through the referer from header, we can safely narrow down LDAP queries.
        referer = referer = req.args.get('referer') or req.get_header('Referer')
        if referer:
            return template, data, None

        uid = req.authname.lower()
        try:
            name, email = self._getUserAttributes(uid)
            req.session['name'] = name.decode('utf-8')
            req.session['email'] = email
            self.log.info('Update user info from LDAP. URL: %s, user: %s.' % (req.path_info, uid))
        except:
            self.log.error('Search LDAP problems. Check trac.ini ldap options')
        return template, data, None
    #
    #----------------------------------------------------------- helper methods
    #
    def _getUserAttributes(self, uid):
        """Get CommonName, mail from LDAP.
        """
        filter = '%s=%s' % (self.userFilter, uid)
        result = []
        id = self.ldap.search(self.basedn, ldap.SCOPE_SUBTREE, filter, None)
        type, data = self.ldap.result(id, 0)
        self.log.info('%s - %s' % (data[0][1]['cn'][0], data[0][1]['mail'][0]))
        return (data[0][1]['cn'][0], data[0][1]['mail'][0])
