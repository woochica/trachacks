# Copyright 2006, Waldemar Kornewald <wkornew@gmx.net>
# with modifications by Jonathan Daugherty <cygnus@janrain.com>
# Distributed under the terms of the MIT License.

import re
import time
import thread
import cPickle

from openid.store import sqlstore
from openid.consumer import consumer
from yadis.discover import DiscoveryFailure
from urljr.fetchers import HTTPFetchingError

from trac.config import *
from trac.core import *
from trac.db import *
from trac.env import IEnvironmentSetupParticipant
from trac.web.api import IAuthenticator, IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.util import escape, hex_entropy, TracError, Markup

class TracOpenIDStore(sqlstore.SQLStore):
    """
    An SQLStore subclass for storing OpenID association data.  This
    doesn't use the Trac database schema specification idiom, because
    at the time of this writing, the trac sqlite backend ignores size
    specifications on columns, which are needed for these tables.
    """

    create_nonce_sql = """
    CREATE TABLE %(nonces)s
    (
        nonce CHAR(8) UNIQUE PRIMARY KEY,
        expires INTEGER
    )"""

    create_assoc_sql = """
    CREATE TABLE %(associations)s
    (
        server_url BLOB,
        handle VARCHAR(255),
        secret BLOB,
        issued INTEGER,
        lifetime INTEGER,
        assoc_type VARCHAR(64),
        PRIMARY KEY (server_url, handle)
    )"""

    create_settings_sql = """
    CREATE TABLE %(settings)s
    (
        setting VARCHAR(128) UNIQUE PRIMARY KEY,
        value BLOB
    )"""

    create_auth_sql = 'INSERT INTO %(settings)s VALUES ("auth_key", %%s);'
    get_auth_sql = 'SELECT value FROM %(settings)s WHERE setting = "auth_key";'

    set_assoc_sql = ('REPLACE INTO %(associations)s '
                     'VALUES (%%s, %%s, %%s, %%s, %%s, %%s);')
    get_assocs_sql = ('SELECT handle, secret, issued, lifetime, assoc_type'
                      ' FROM %(associations)s WHERE server_url = %%s;')
    get_assoc_sql = (
        'SELECT handle, secret, issued, lifetime, assoc_type'
        ' FROM %(associations)s WHERE server_url = %%s AND handle = %%s;')
    remove_assoc_sql = ('DELETE FROM %(associations)s '
                        'WHERE server_url = %%s AND handle = %%s;')

    add_nonce_sql = 'REPLACE INTO %(nonces)s VALUES (%%s, %%s);'
    get_nonce_sql = 'SELECT * FROM %(nonces)s WHERE nonce = %%s;'
    remove_nonce_sql = 'DELETE FROM %(nonces)s WHERE nonce = %%s;'

    def blobDecode(self, blob):
        """
        Decode a blob from the database.
        """
        return str(blob)

    def blobEncode(self, s):
        """
        Encode a blob so it can be inserted safely.
        """
        return buffer(s)

class OpenIDLoginModule(Component):
    """Handles OpenID identification for Trac."""

    implements(IAuthenticator, INavigationContributor, IRequestHandler,
               ITemplateProvider, IEnvironmentSetupParticipant)

    require_personal_details = BoolOption('openid',
        'require_personal_details', 'true',
        """Whether we should ask the ID provider for the user's
        full name and email address.""")

    # This key is used to store pickled OpenID state information in
    # the trac session.
    openid_session_key = 'openid_session_data'

    def __init__(self):
        db = self.env.get_db_cnx()
        self.store = self._getStore(db)

    def _getStore(self, db):
        return TracOpenIDStore(db)

    def _initStore(self, db):
        self._getStore(db).createTables()

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        db = self.env.get_db_cnx()
        self._initStore(db)
        db.commit()

    def environment_needs_upgrade(self, db):
        c = db.cursor()
        try:
            c.execute("SELECT count(*) FROM oid_associations")
            return False
        except Exception, e:
            db.rollback()
            return True

    def upgrade_environment(self, db):
        self._initStore(db)

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
 
    def _getConsumer(self, req):
        s = self._get_session(req)
        return consumer.Consumer(s, self.store), s

    def _start_login(self, req, url):
        """Initiates OpenID login phase."""
        oidconsumer, session = self._getConsumer(req)
        try:
            authreq = oidconsumer.begin(url)
        except (HTTPFetchingError, DiscoveryFailure):
            req.hdf['auth.message'] = 'Failed to retrieve identity: %s' % url
            return False

        self._commit_session(session, req)

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
        oidconsumer, session = self._getConsumer(req)
        response = oidconsumer.complete(req.args)
        self._commit_session(session, req)

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
        """Returns a session dict that can store any kind of object."""
        try:
            return cPickle.loads(str(req.session[self.openid_session_key]))
        except KeyError:
            return {}

    def _commit_session(self, session, req):
        req.session[self.openid_session_key] = str(cPickle.dumps(session))
