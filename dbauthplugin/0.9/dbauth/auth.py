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
# Author: Brad Anderson <brad@dsource.org>

import re
import time

from dbauth.env import *

from trac.core import *
from trac.web.api import IAuthenticator, IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.util import escape, hex_entropy, TracError, Markup


class DbAuthLoginModule(Component):
    """Implements user authentication based on database tables and an HTML form,
    combined with cookies for communicating the login information across the whole site.
    """

    implements(IAuthenticator, INavigationContributor, ITemplateProvider, IRequestHandler)

    def __init__(self):
        self.envname = get_envname(self.env)
        
    # IAuthenticator methods

    def authenticate(self, req):
        authname = None
        if req.remote_user:
            authname = req.remote_user
        elif req.incookie.has_key('trac_db_auth'):
            authname = self._get_name_for_cookie(req, req.incookie['trac_db_auth'])

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
            yield 'metanav', 'login', 'logged in as %s' % req.authname
            yield 'metanav', 'logout', Markup( '<a href="%s">Logout</a>' \
                  % escape(self.env.href.logout()) )
        else:
            yield 'metanav', 'login', Markup( '<a href="%s">Login</a>' \
                  % escape(self.env.href.login()) )

    # IRequestHandler methods

    def match_request(self, req):
        return re.match('/(login|logout)/?', req.path_info)

    def process_request(self, req):
        if req.method == 'POST':
            if req.args.get('login'):
                uid, pwd = req.args.get('uid'), req.args.get('pwd')
                if self._check_login(uid, pwd):
                    self._do_login(req)
                    req.redirect(self.env.href.wiki())
                else:
                    req.hdf["auth.message"] = "Login Incorrect"
                            

        if req.path_info.startswith('/login'):
            # self._do_login(req)
            template = "login.cs"
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
        sql = """SELECT username
                 FROM trac_users
                 WHERE username= %s and password = %s
                   AND (envname = %s or envname='all')"""
        cursor.execute(sql, (uid, pwd, self.envname))
        row = cursor.fetchone()        
        if not row:
            ret = False
        else:
            ret = True
            
        return ret

    def _do_login(self, req):
        """Log the remote user in."""
        
        remote_user, pwd = req.args.get('uid'), req.args.get('pwd')
        remote_user = remote_user.lower()

        cookie = hex_entropy()
        db = get_db(self.env)
        cursor = db.cursor()
        cursor.execute("INSERT INTO trac_cookies "
                       "(envname, cookie, username, ipnr, unixtime) "
                       "VALUES (%s, %s, %s, %s, %s)", (self.envname, cookie, remote_user,
                       req.remote_addr, int(time.time())))
        db.commit()

        req.authname = remote_user
        req.outcookie['trac_db_auth'] = cookie
        req.outcookie['trac_db_auth']['expires'] = 100000000
        req.outcookie['trac_db_auth']['path'] = self.env.href()

    def _do_logout(self, req):
        """Log the user out.

        Simply deletes the corresponding record from the auth_cookie table.
        """
        if req.authname == 'anonymous':
            # Not logged in
            return

        db = get_db(self.env)
        cursor = db.cursor()
        cursor.execute("DELETE FROM trac_cookies "
                       "WHERE username=%s "
                       "  AND envname=%s",
                       (req.authname, self.envname))
        db.commit()
        self._expire_cookie(req)

    def _expire_cookie(self, req):
        """Instruct the user agent to drop the auth cookie by setting the
        "expires" property to a date in the past.
        """
        req.outcookie['trac_db_auth'] = ''
        req.outcookie['trac_db_auth']['path'] = self.env.href()
        req.outcookie['trac_db_auth']['expires'] = -10000

    def _get_name_for_cookie(self, req, cookie):
        db = get_db(self.env)
        cursor = db.cursor()
        cursor.execute("SELECT username FROM trac_cookies "
                       "WHERE cookie=%s AND envname=%s",
                           (cookie.value,self.envname))
        row = cursor.fetchone()
        if not row:
            # The cookie is invalid (or has been purged from the database), so
            # tell the user agent to drop it as it is invalid
            self._expire_cookie(req)
            return None

        return row[0]

    def _redirect_back(self, req):
        """Redirect the user back to the URL she came from."""
        referer = req.get_header('Referer')
        if referer and not referer.startswith(req.base_url):
            # only redirect to referer if the latter is from the same
            # instance
            referer = None
        req.redirect(referer or self.env.abs_href())



    