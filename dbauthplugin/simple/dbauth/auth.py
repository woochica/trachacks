# -*- coding: utf-8 -*-
#
# Copyright 2007 Waldemar Kornewald
# All rights reserved. Distributed under the terms of the MIT license.

import re
import time
import md5
import sha

from trac.core import *
from trac.config import *
from trac.db import *
from trac.web.api import IAuthenticator
from trac.web.main import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.util import escape, hex_entropy, Markup


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
    algorithm = Option('dbauth', 'algorithm', 'sha',
        """Choose which hash algorithm to use. Possible options:
        md5, sha""")

    session_lifetime = 7 * 24 * 60 * 60

    def __init__(self):
        self.users = {
           'table': self.env.config.get('dbauth', 'users_table', 'trac_users'),
           'username': self.env.config.get('dbauth','username_field', 'username'),
           'password': self.env.config.get('dbauth','password_field', 'password'),
           'email': self.env.config.get('dbauth','email_field', None)}
        if self.algorithm == 'sha':
            self.crypt = sha
        else:
            self.crypt = md5


    # IAuthenticator methods

    def authenticate(self, req):
        authname = None
        if req.incookie.has_key('db_auth'):
            authname = self._get_name_for_cookie(req,
                                    req.incookie.get('db_auth').value)

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
                            % req.href.password())
            yield 'metanav', 'logout', Markup('<b><a href="%s">Logout</a></b>' \
                  % req.href.logout())
        else:
            yield 'metanav', 'login', Markup('<b><a href="%s">Login</a></b>' \
                  % req.href.login())

    # IRequestHandler methods

    def match_request(self, req):
        return (self.password_changeable \
                and req.path_info == '/password') \
                or req.path_info == '/logout' \
                or req.path_info == '/login'

    def process_request(self, req):
        referer = req.args.get('referer') or req.get_header('Referer')
        if not referer or referer.endswith('/login') or \
                referer.endswith('/settings') or len(referer) == 0:
            referer = req.href()

        data = {'referer': referer, 'login_error': None}

        if req.method == 'POST':
            if req.args.get('login'):
                uid, pwd = req.args.get('user').lower(), req.args.get('password')
                if self._check_login(uid, pwd):
                    self._do_login(req, uid)
                    req.redirect(referer)
                else:
                    data['login_error'] = 'Wrong username or password. Please try again.'
            else:
                data['login_error'] = 'Could not understand your command. Did you really use this web form?'

        if req.path_info.startswith('/login'):
            template = "login.html"
        elif req.path_info.startswith('/logout'):
            self._do_logout(req)
            req.redirect(referer)
        return template, data, None

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # Internal methods

    def _check_login(self, uid, pwd):
        db = get_db(self.env)
        cursor = db.cursor()
        sql = "SELECT %s FROM %s WHERE LOWER(%s) = LOWER(%%s)" % \
              (self.users['password'], self.users['table'],
               self.users['username'])
        cursor.execute(sql, (uid,))
        hash = self.crypt.new(pwd).hexdigest()
        for row in cursor:
            if row[0] == hash:
                return True

        return False

    def _do_login(self, req, remote_user):
        """Log the remote user in."""

        cookie = hex_entropy()
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("INSERT INTO auth_cookie "
                       "(cookie ,name ,ipnr ,time) "
                       "VALUES (%s, %s, %s, %s)",
                       (cookie, remote_user, req.remote_addr,
                        int(time.time())))
        db.commit()

        req.outcookie['db_auth'] = cookie
        req.outcookie['db_auth']['path'] = req.href()
        req.outcookie['db_auth']['expires'] = 100000000

        self._update_email(remote_user)

    def _do_logout(self, req):
        """Log the user out.

        Simply deletes the corresponding record from the auth_cookie table.
        """
        if req.authname == 'anonymous':
            # Not logged in
            return

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("DELETE FROM auth_cookie "
                       "WHERE LOWER(name) = LOWER(%s) OR time < %s",
                       (req.authname, int(time.time()) - self.session_lifetime))
        db.commit()
        self._expire_cookie(req)

    def _expire_cookie(self, req):
        """Instruct the user agent to drop the auth cookie by setting the
        "expires" property to a date in the past."""
        req.outcookie['db_auth'] = ''
        req.outcookie['db_auth']['path'] = req.href()
        req.outcookie['db_auth']['expires'] = -10000

    def _get_name_for_cookie(self, req, cookie):
        """Finds out the name of the user with the given cookie.
        Also handles cookie expiration. The session is refreshed every hour,
        so if you regularly use Trac you stay logged in forever."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT name, time FROM auth_cookie "
                       "WHERE cookie = %s",
                       (cookie,))
        row = cursor.fetchone()
        if not row or row[1] < int(time.time()) - self.session_lifetime:
            # the cookie has become invalid
            cursor.execute("DELETE FROM auth_cookie "
                           "WHERE time < %s",
                           (int(time.time()) - self.session_lifetime,))
            db.commit()
            self._expire_cookie(req)
            return None
        elif row[1] < int(time.time()) - 60 * 60:
            # refresh session
            cursor.execute("UPDATE auth_cookie "
                           "SET time = %s, ipnr = %s "
                           "WHERE cookie = %s",
                           (int(time.time()), req.remote_addr, cookie))
            db.commit()
            req.outcookie['db_auth'] = cookie
            req.outcookie['db_auth']['path'] = req.href()
            req.outcookie['db_auth']['expires'] = 100000000
            # Don't forget to check whether we have a new email address.
            self._update_email(row[0])

        return row[0]

    def _update_email(self, user):
        email_field = self.users['email']
        if not email_field or len(email_field) == 0:
            return
        db = get_db(self.env)
        cursor = db.cursor()
        sql = "SELECT %s FROM %s WHERE %s = %%s" % \
              (email_field, self.users['table'],
               self.users['username'])
        cursor.execute(sql, (user,))
        row = cursor.fetchone()
        if not row or not row[0]:
            return
        email = row[0]
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("DELETE FROM session_attribute "
                       "WHERE name='email' AND sid=%s AND authenticated=1",
                       (user,))
        cursor.execute("INSERT INTO session_attribute "
                       "(sid, authenticated, name, value) "
                       "VALUES (%s, 1, 'email', %s)",
                       (user, email))
        db.commit()
