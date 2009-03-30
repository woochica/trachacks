#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 Copyright (C) 2008 General de Software de Canarias.
 
 Author: Carlos López Pérez <carlos.lopezperez@gmail.com>
"""

import re, ldap

from genshi.builder import tag
from trac.core import implements, Component
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider

class AccountLDAP(Component):
    """Gestiona el api para la interacción con el LDAP y la gestión del trac
    """
    implements(IRequestFilter, INavigationContributor, ITemplateProvider,
               IRequestHandler)
    
    MODULE_NAME = 'accountldap'    
    
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
                self.ldap.simple_bind(self.config.get('ldap', 'bind_user'),  
                                      self.config.get('ldap', 'bind_passwd'))
                break
            except ldap.LDAPError, e:
                self.log.error('Connection LDAP problems. Check trac.ini ldap options. Attempt', (i + 1))
                self.enabled = False
        self.log.info('Connection LDAP basdn %s" userdn "%s". Attempt %i' % (self.basedn, 
                                                                 self.userdn, (i + 1)))
        
    #
    #------------------------------------------------- IRequestFilter interface
    #
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if not req.remote_user or req.session.has_key('email'):
            return template, data, content_type 
        uid = req.remote_user.lower()
        name, email = self._getUserAttributes(uid)
        req.session['name'] = name        
        req.session['email'] = email
        return template, data, content_type        
    #
    #----------------------------------------- INavigationContributor interface
    #
    def get_active_navigation_item(self, req):
        return self.MODULE_NAME
                
    def get_navigation_items(self, req):
        if not req.authname or not req.session.has_key('email'):
            return
        yield ('metanav', self.MODULE_NAME,
               tag.a(u'Contraseñas', href=req.href.accountldap()))
    #
    #------------------------------------------------ IRequestHandler interface
    #
    def match_request(self, req):
        return re.match(r'/%s(?:_trac)?(?:/.*)?$' % self.MODULE_NAME, req.path_info)

    def process_request(self, req):
        data = {'accountldap_message': None}
        template = '%s.html' % self.MODULE_NAME        
        if req.method != 'POST':
            return template, data, None
        p1 = req.args.get('password1')
        p2 = req.args.get('password2')
        old = req.args.get('oldpassword')
        if p1 != p2:
            data['accountldap_message'] = tag.center(u'Las contraseñas suministradas no coinciden.', tag.b(u' Por favor, revise las contraseñas.'), style='color:chocolate')
            return template, data, None
        if old == p1:
            data['accountldap_message'] = tag.center(u'Las contraseña antigua y la nueva contraseña es la misma.', tag.b(u' Por favor, realice un cambio en la nueva contraseña.'), style='color:chocolate')
            return template, data, None
        dn = '%s=%s,%s,%s' % (self.userFilter, req.authname, self.userdn, self.basedn)
        try:
            self.log.warn('Ldap change password dn. %s' % dn)
            self.ldap.passwd_s(dn, old, p1)
        except ldap.LDAPError, e:
            data['accountldap_message'] = tag.center(u'Se produjo un error durante el cambio de contraseña.', tag.b(u' Por favor, comprueba que la contraseña antigua es la correcta.'), style='color:chocolate')
            self.log.warn('Ldap change password. %s' % e)
            return template, data, None
        data['accountldap_message'] = tag.center(tag.b(u'La contraseña se ha cambiado correctamente.'), style='color:green')        
        return template, data, None
    #
    #---------------------------------------------- ITemplateProvider interface
    #
    def get_htdocs_dirs(self): 
        return []
     
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    #
    #----------------------------------------------------------- helper methods
    #
    def _getUserAttributes(self, uid):
        """Devuelve el nombre completo y el correo definido en el ldap
        """
        filter = '%s=%s' % (self.userFilter, uid)
        result = []
        try:
            id = self.ldap.search(self.basedn, ldap.SCOPE_SUBTREE, filter, None)
            type, data = self.ldap.result(id, 0)
        except ldap.LDAPError, e:
            self.log.error('Search LDAP problems. Check trac.ini ldap options')
            return ('', '')
        self.log.info('%s - %s' % (data[0][1]['cn'][0], data[0][1]['mail'][0]))
        return (data[0][1]['cn'][0], data[0][1]['mail'][0])