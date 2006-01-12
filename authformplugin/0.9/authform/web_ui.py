# -*- coding: iso8859-1 -*-
#
# Copyright (C) 2003-2005 Edgewall Software
# Copyright (C) 2003-2005 Jonas Borgström <jonas@edgewall.com>
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
# Author: Jonas Borgström <jonas@edgewall.com 
# Author: Andrew Deason <adeason@tjhsst.edu>

from __future__ import generators
import re
import time
import urllib2,base64

from trac.core import *
from trac.web.api import IAuthenticator, IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.util import escape, hex_entropy, TRUE, Markup


class LoginFormModule(Component):
    """Implements user authentication based on HTTP authentication provided by
    the web-server, combined with cookies for communicating the login
    information across the whole site. This module makes an internal request to
    the webserver using HTTP authentication, instead of using HTTP
    authentication directly from the user, so the user has the ability to
    logout.

    This mechanism expects that the web-server is setup so that a request to the
    path '/login' requires authentication (just Basic authentication for now).
    When a user attempts to login, this module attempts to use that information
    to authenticate to the page https://trac.company.com/login, using HTTP
    authentication. If it is successful, a 'trac_auth' cookie is stored in the
    user's browser. This cookie is used to identify the user in subsequent
    requests, until it is destroyed when the user logs out.
    """

    implements(IAuthenticator, INavigationContributor, IRequestHandler, ITemplateProvider)

    # IAuthenticator methods

    def authenticate(self, req):
        authname = None
        if req.incookie.has_key('trac_auth'):
            authname = self._get_name_for_cookie(req, req.incookie['trac_auth'])

        if not authname:
            return None

        ignore_case = self.env.config.get('trac', 'ignore_auth_case')
        ignore_case = ignore_case.strip().lower() in TRUE
        if ignore_case:
            authname = authname.lower()
        return authname

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'login'

    def get_navigation_items(self, req):
        if req.authname and req.authname != 'anonymous':
            yield 'metanav', 'login', 'logged in as %s' % escape(req.authname)
            yield 'metanav', 'logout', Markup('<a href="%s">Logout</a>' \
                  % escape(self.env.href.logout()))
        else:
            yield 'metanav', 'login', Markup('<a href="%s">Login</a>' \
                  % escape(self.env.href.login()))

    # IRequestHandler methods

    def match_request(self, req):
        return re.match('/(login|logout)/?', req.path_info)

    def process_request(self, req):
        if req.path_info.startswith('/login'):
            if not self._do_login(req):
	    	return 'authform.cs', None
        elif req.path_info.startswith('/logout'):
            self._do_logout(req)
        self._redirect_back(req)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
    return []

    # Internal methods

    def _do_login(self, req):
        """Log the remote user in.
	
	This function displays a form to the user to log themselves in, and
	verifies the information when the user submits that form. If the
	authentication is successful, the user name is inserted into the
	`auth_cookie` table and a cookie identifying the user on subsequent
	requests is sent back to the client.

        If the Authenticator was created with `ignore_case` set to true, then 
        the authentication name passed from the web form 'username' variable
        will be converted to lower case before being used. This is to avoid
        problems on installations authenticating against Windows which is not
        case sensitive regarding user names and domain names
        """

	if req.args.get('username'):
		assert req.args.get('password'), 'No password'
		# Test authentication

		try:
			self._try_http_auth(req.base_url[:req.base_url.find('/',8)] + '/login',req.args.get('username'),req.args.get('password'))
		except IOError, e:
			# Incorrect password
			req.hdf['title'] = 'Login Failed'
			req.hdf['login.action'] = self.env.href() + '/login'
			req.hdf['login.referer'] = req.args.get('ref')
			req.hdf['login.error'] = 'Invalid username or password'
			return None

		# Successful authentication, set cookies and stuff
	        remote_user = req.args.get('username')
	        ignore_case = self.env.config.get('trac', 'ignore_auth_case')
	        ignore_case = ignore_case.strip().lower() in TRUE
	        if ignore_case:
	            remote_user = remote_user.lower()
	
	        assert req.authname in ('anonymous', remote_user), \
	               'Already logged in as %s.' % req.authname
	
	        cookie = hex_entropy()
	        db = self.env.get_db_cnx()
	        cursor = db.cursor()
	        cursor.execute("INSERT INTO auth_cookie (cookie,name,ipnr,time) "
	                       "VALUES (%s, %s, %s, %s)", (cookie, remote_user,
	                       req.remote_addr, int(time.time())))
	        db.commit()
	
	        req.authname = remote_user
	        req.outcookie['trac_auth'] = cookie
	        req.outcookie['trac_auth']['path'] = self.env.href()
        	req.redirect(req.args.get('ref'))
	else:
		# No authentication information passed, display a form
		req.hdf['title'] = 'Login'
		req.hdf['login.action'] = self.env.href() + '/login'
		req.hdf['login.referer'] = req.get_header('Referer')
		return None
	
    def _do_logout(self, req):
        """Log the user out.

        Simply deletes the corresponding record from the auth_cookie table.
        """
        if req.authname == 'anonymous':
            # Not logged in
            return

        # While deleting this cookie we also take the opportunity to delete
        # cookies older than 10 days
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("DELETE FROM auth_cookie WHERE name=%s OR time < %s",
                       (req.authname, int(time.time()) - 86400 * 10))
        db.commit()
        self._expire_cookie(req)
	req.remote_user = 'anonymous'
	req.remote_pass = ''

    def _try_http_auth(self, uri, user, passw):
        authreq = urllib2.Request(uri)
        base64string = base64.encodestring('%s:%s' % (user, passw))[:-1]
	authheader = "Basic %s" % base64string
	authreq.add_header("Authorization", authheader)
	handle = urllib2.urlopen(authreq)

    def _expire_cookie(self, req):
        """Instruct the user agent to drop the auth cookie by setting the
        "expires" property to a date in the past.
        """
        req.outcookie['trac_auth'] = ''
        req.outcookie['trac_auth']['path'] = self.env.href()
        req.outcookie['trac_auth']['expires'] = -10000

    def _get_name_for_cookie(self, req, cookie):
        check_ip = self.env.config.get('trac', 'check_auth_ip')
        check_ip = check_ip.strip().lower() in TRUE

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        if check_ip:
            cursor.execute("SELECT name FROM auth_cookie "
                           "WHERE cookie=%s AND ipnr=%s",
                           (cookie.value, req.remote_addr))
        else:
            cursor.execute("SELECT name FROM auth_cookie WHERE cookie=%s",
                           (cookie.value,))
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
