# Copyright 2006, Waldemar Kornewald <wkornew@gmx.net>
# Distributed under the terms of the MIT License.

import re
import time
import thread

from openid.store import dumbstore
from openid.consumer import consumer
from yadis.discover import DiscoveryFailure
from urljr.fetchers import HTTPFetchingError

from trac.config import *
from trac.core import *
from trac.db import *
from trac.web.api import IAuthenticator, IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.util import escape, hex_entropy, TracError, Markup


class OpenIDLoginModule(Component):
    """Handles OpenID identification for Trac."""

    implements(IAuthenticator, INavigationContributor, IRequestHandler,
               ITemplateProvider)

    sessions = {}
    require_personal_details = BoolOption('openid',
        'require_personal_details', 'true',
        """Whether we should ask the ID provider for the user's
        full name and email address.""")

    def __init__(self):
        self.lock = thread.allocate_lock()

    # IAuthenticator methods

    def authenticate(self, req):
        if req.incookie.has_key('trac_auth'):
            return self._get_name_for_cookie(req, req.incookie['trac_auth'])

        return None

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'login'

    def get_navigation_items(self, req):
        if req.authname and req.authname != 'anonymous':
            yield 'metanav', 'login', Markup('logged in as <b>%s</b>' \
                                        % req.authname)
            yield 'metanav', 'logout', Markup('<b><a href="%s">Logout</a></b>' \
                                        % escape(self.env.href.logout()))
        else:
            yield 'metanav', 'login', Markup('<a href="%s">Login</a>' \
                                        % escape(self.env.href.login()))

    # IRequestHandler methods

    def match_request(self, req):
        return re.match('/(login|openid_return|logout)/?', req.path_info)

    def process_request(self, req):
        req.hdf['auth.handler'] = self.env.href.login()
        if req.path_info.startswith('/login'):
            if req.method == 'POST':
                self._start_login(req, req.args.get('openid_url'))

            return 'login.cs', None
        elif req.path_info.startswith('/openid_return'):
            self._handle_return(req)
            return 'login.cs', None
        elif req.path_info.startswith('/logout'):
            self._logout(req)
            req.redirect(self.env.href.login())
        return None, None

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('openidauth', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # Internal methods

    def _getTrustRoot(self, req):
        href = req.href()
        if href:
            base_url = req.abs_href()[:-len(href)]
        else:
            base_url = req.abs_href()

        return base_url

    def _getReturnTo(self, req):
        return self._getTrustRoot(req) + self.env.href.openid_return()
 
    def _start_login(self, req, url):
        """Initiates OpenID login phase."""
        oidconsumer = consumer.Consumer(self._get_session(req), self._get_store())
        try:
            authreq = oidconsumer.begin(url)
        except (HTTPFetchingError, DiscoveryFailure):
            req.hdf['auth.message'] = 'Failed to retrieve identity: %s' % url
            return False

        if self.require_personal_details:
            # tell the IdP that we need the user's email address
            authreq.addExtensionArg('sreg', 'required', 'email')
            # optionally, the user's full name would be nice, too
            authreq.addExtensionArg('sreg', 'optional', 'fullname')

        req.redirect(authreq.redirectURL(self._getTrustRoot(req), self._getReturnTo(req)))
        return True

    def _handle_return(self, req):
        """Handles the final login step.
        
        The IdP sends the user back to us."""
        oidconsumer = consumer.Consumer(self._get_session(req), self._get_store())
        response = oidconsumer.complete(req.args)
        if response.status == consumer.SUCCESS:
            if response.getReturnTo().split('?')[0] == self._getReturnTo(req):
                self._login(req, response)
                req.redirect(self.env.href())
                return True

        # we only get here if authentication failed
        req.hdf['auth.message'] = 'Login failed!'
        return False

    def _login(self, req, response):
        """Store login information into session."""
        cookie = hex_entropy()
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('INSERT INTO auth_cookie ' \
                       '(cookie ,name ,ipnr ,time) ' \
                       'VALUES (%s, %s, %s, %s)',
                       (cookie, response.identity_url,
                        req.remote_addr, int(time.time())))
        db.commit()

        req.outcookie['trac_auth'] = cookie
        req.outcookie['trac_auth']['path'] = self.env.href()
        req.outcookie['trac_auth']['expires'] = 60 * 60 * 24

        # update user's contact details
        info = response.extensionResponse('sreg')
        if info and info.has_key('fullname') and len(info['fullname']) > 0:
            req.session['name'] = info['fullname']
        if info and info.has_key('email') and len(info['email']) > 0:
            req.session['email'] = info['email']

    def _logout(self, req):
        """Remove the login session information."""
        # only logout authenticated users
        if req.authname == 'anonymous':
            return

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('DELETE FROM auth_cookie ' \
                       'WHERE name=%s OR time < %s',
                       (req.authname, int(time.time()) - 60 * 60 * 24))
        db.commit()
        self._expire_cookie(req)

    def _expire_cookie(self, req):
        req.outcookie['trac_auth'] = ''
        req.outcookie['trac_auth']['path'] = self.env.href()
        req.outcookie['trac_auth']['expires'] = -10000

    def _get_name_for_cookie(self, req, cookie):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT name FROM auth_cookie ' \
                       'WHERE cookie=%s AND ipnr=%s',
                       (cookie.value, req.remote_addr))
        row = cursor.fetchone()
        if not row:
            # the cookie has become invalid
            self._expire_cookie(req)
            return None

        return row[0]

    def _get_session(self, req):
        """Returns a session dict that can store any kind of object.
        
        This is a hack to get around the OpenID library's limitations."""

        # we must be thread-safe
        self.lock.acquire()
        
        # first get rid of old sessions
        now = int(time.time())
        for k, v in self.sessions.items():
            if v['_last_access'] + 3 * 60 < now:
                del self.sessions[k]
        
        # now find an existing session or create a new one
        session = {}
        sid = req.session.sid
        if self.sessions.has_key(sid):
            session = self.sessions[sid]
        else:
            self.sessions[sid] = session

        session['_last_access'] = now
        self.lock.release()

        return session

    def _get_store(self):
        return dumbstore.DumbStore('afsnjtq4tq9n3klt1gngasd9fasn43')
