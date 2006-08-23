# -*- coding: iso8859-1 -*-
#
# Copyright (C) 2003-2005 Edgewall Software
# Copyright (C) 2003-2005 Jonas Borgström <jonas@edgewall.com>
# Copyright (C) 2006 Brad Anderson <brad@dsource.org>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Authors: Brad Anderson <brad@dsource.org>
#          Waldemar Kornewald <wkornew@gmx.net>

import re
import time
import sha

from trac.core import *
from trac.db import *
from trac.web.api import IAuthenticator, IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.util import escape, hex_entropy, TracError, Markup


def get_db(env):
    """Return a database connection"""
    return CentralDatabaseManager(env).get_connection()

class CentralDatabaseManager(DatabaseManager):
    connection_uri = Option('dbauth', 'database', 'sqlite:db/trac.db',
        """Database connection
        [wiki:TracEnvironment#DatabaseConnectionStrings string] for this
        project""")


class DbAuthLoginModule(Component):
    """Implements user authentication based on database tables and an
    HTML form, combined with cookies for communicating the login information
    across the whole site."""

    implements(IAuthenticator, INavigationContributor, ITemplateProvider, 
               IRequestHandler)

    password_changeable = BoolOption('dbauth', 'password_changeable', 'false',
        """Allow user to change his password.""")

    def __init__(self):
        self.users = {
           'table': self.env.config.get('dbauth', 'users_table', 'trac_users'),
           'username': self.env.config.get('dbauth','username_field', 'username'),
           'password': self.env.config.get('dbauth','password_field', 'password'),
           'email': self.env.config.get('dbauth','email_field', None)}


    # IAuthenticator methods

    def authenticate(self, req):
        authname = None
        if req.incookie.has_key('db_auth'):
            authname = self._get_name_for_cookie(req, req.incookie['db_auth'])

        if not authname:
            return None

        if self.config.getbool('trac', 'ignore_auth_case'):
            authname = authname.lower()

        return authname

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'login'

    def get_navigation_items(self, req):
        if req.authname and req.authname != 'anonymous':
            yield 'metanav', 'login', Markup('logged in as <b>%s</b>' \
                    % req.authname)
            if self.password_changeable:
                yield 'metanav', 'password', \
                    Markup('<a href="%s">Password</a>' \
                            % escape(self.env.href.password()))
            yield 'metanav', 'logout', Markup('<b><a href="%s">Logout</a></b>' \
                  % escape(self.env.href.logout()))
        else:
            yield 'metanav', 'login', Markup('<b><a href="%s">Login</a></b>' \
                  % escape(self.env.href.login()))

    # IRequestHandler methods

    def match_request(self, req):
        if req.authname and req.authname != 'anonymous':
            return (self.password_changeable \
                    and req.path_info == '/password') \
                    or req.path_info == '/logout'
        else:
            return req.path_info == '/login'

    def process_request(self, req):
        if req.method == 'POST':
            if req.args.get('login'):
                uid, pwd = req.args.get('uid'), req.args.get('pwd')
                if self._check_login(uid, pwd):
                    self._do_login(req)
                    req.redirect(req.href())
                else:
                    req.hdf['auth.message'] = 'Login Incorrect'
            elif req.args.get('password'):
                old, new, repeat = req.args.get('opwd'), req.args.get('npwd'), req.args.get('rpwd')
                if not new or len(new) < 5:
                    req.hdf['auth.message'] = 'New password too short'
                elif new != repeat:
                    req.hdf['auth.message'] = 'Repeated password does not match'
                elif not self._check_login(req.authname, old):
                    req.hdf['auth.message'] = 'Wrong Password'
                else:
                    req.hdf['auth.message'] = 'Password Changed'
                    self._change_password(req, new)

        if req.path_info.startswith('/login'):
            # self._do_login(req)
            template = "login.cs"
        elif req.path_info.startswith('/password'):
            template = 'password.cs'
        elif req.path_info.startswith('/logout'):
            self._do_logout(req)
            req.redirect(self.env.href.login())
        return template, None

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('dbauth', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # Internal methods

    def _check_login(self, uid, pwd):
        db = get_db(self.env)
        cursor = db.cursor()
        sql = 'SELECT %s FROM %s WHERE %s = %%s' % \
              (self.users['password'], self.users['table'],
               self.users['username'])
        cursor.execute(sql, (uid,))
        hash = sha.new(pwd).hexdigest()
        for row in cursor:
            if row[0] == hash:
                return True

        return False

    def _do_login(self, req):
        """Log the remote user in."""

        remote_user = req.args.get('uid')

        cookie = hex_entropy()
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('INSERT INTO auth_cookie ' \
                       '(cookie ,name ,ipnr ,time) ' \
                       'VALUES (%s, %s, %s, %s)',
                       (cookie, remote_user, req.remote_addr,
                        int(time.time())))
        db.commit()

        req.outcookie['db_auth'] = cookie
        req.outcookie['db_auth']['path'] = self.env.href()
        req.outcookie['db_auth']['expires'] = 100000000

        self._update_email(req, remote_user)

    def _do_logout(self, req):
        """Log the user out.

        Simply deletes the corresponding record from the auth_cookie table.
        """
        if req.authname == 'anonymous':
            # Not logged in
            return

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('DELETE FROM auth_cookie ' \
                       'WHERE name = %s OR time < %s',
                       (req.authname, int(time.time()) - 60 * 60 * 24))
        db.commit()
        self._expire_cookie(req)

    def _expire_cookie(self, req):
        """Instruct the user agent to drop the auth cookie by setting the
        "expires" property to a date in the past."""
        req.outcookie['db_auth'] = ''
        req.outcookie['db_auth']['path'] = self.env.href()
        req.outcookie['db_auth']['expires'] = -10000

    def _get_name_for_cookie(self, req, cookie):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT name FROM auth_cookie ' \
                       'WHERE cookie = %s AND ipnr = %s AND time > %s',
                       (cookie.value, req.remote_addr,
                        int(time.time()) - 60 * 60 * 24))
        row = cursor.fetchone()
        if not row:
            # the cookie has become invalid
            self._expire_cookie(req)
            return None

        return row[0]

    def _update_email(self, req, user):
        email_field = self.users['email']
        if not email_field or len(email_field) == 0:
            return
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = 'SELECT %s FROM %s WHERE %s = %%s' % \
              (email_field, self.users['table'],
               self.users['username'])
        cursor.execute(sql, (user,))
        row = cursor.fetchone()
        if not row or not row[0]:
            return
        req.session['email'] = row[0]

    def _change_password(self, req, newpwd):
        if req.authname == 'anonymous':
            # Not logged in
            return

        # change the password
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        newpwd = sha.new(newpwd).hexdigest()
        sql = 'UPDATE %s SET %s = %%s WHERE %s = %%s' % \
              (self.users['table'], self.users['password'],
               self.users['username'])
        cursor.execute(sql, (newpwd, req.authname))
        db.commit()
