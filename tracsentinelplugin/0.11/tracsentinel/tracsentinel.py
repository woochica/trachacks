import re
import urllib

from trac.core import *
from trac.config import Option
from trac.web.api import IAuthenticator, IRequestHandler
from trac.web.chrome import INavigationContributor
from trac.util import escape, hex_entropy, Markup
from trac.web.auth import LoginModule
from genshi.builder import tag

from SentinelService_services import *

class Configuration(object):
    def app_id(self):
        return Option('sentinel', 'app_id')

    def login_url(self):
        return Option('sentinel', 'login_url')

    def service_url(self):
        return Option('sentinel', 'service_url')

    def service_username(self):
        return Option('sentinel', 'service_username')

    def service_password(self):
        return Option('sentinel', 'service_password')

class SentinelAuthenticator(object):
    def __init__(self, login_url, app_id, service_url, service_username, service_password):
        self._login_url = login_url
        self._app_id = app_id
        self._service_url = service_url
        self._service_username = service_username
        self._service_password = service_password

    def login_url(self, service):
        return self._login_url + '?App=' + self._app_id + '&service=' + urllib.quote_plus(service)

    def validate_token(self, browser_ip, token):
	loc = SentinelServiceLocator()
	portType = loc.getSentinelEndpoint(self._service_url)

	request = SentinelEndpoint_getCredential()
	request._appID = self._app_id
	request._browserIPAddress = browser_ip
	request._clientPassword = self._service_password
	request._clientUserID = self._service_username
	request._token = token

	response = portType.getCredential(request)

	if response._status._code == 12:
            return (False, None)
        else:
            return (True, response._credential._publicID)

class SentinelLoginModule(LoginModule):
    login_url = Option('sentinel', 'login_url')
    app_id = Option('sentinel', 'app_id')
    service_url = Option('sentinel', 'service_url')
    service_username = Option('sentinel', 'service_username')
    service_password = Option('sentinel', 'service_password')

    def authenticate(self, req):
        token = req.args.get('Token')

        if token:
            valid, user = self.sentinel.validate_token(req.remote_addr, token)

            if valid:
                req.environ['REMOTE_USER'] = user

        return super(SentinelLoginModule, self).authenticate(req)

    def get_navigation_items(self, req):
        if req.authname and req.authname != 'anonymous':
            yield 'metanav', 'login', 'logged in as %s' % req.authname
            yield 'metanav', 'logout', tag.a('Logout', href=req.href.logout())
        else:
            yield 'metanav', 'login', tag.a('Login', href=self.sentinel.login_url(req.abs_href.login()))

    def _do_login(self, req):
        if not req.remote_user:
            req.redirect(self.sentinel.login_url(req.abs_href.login()))

        super(SentinelLoginModule, self)._do_login(req)

        req.redirect(req.abs_href() + '/')

    def _do_logout(self, req):
        if req.authname:
            super(SentinelLoginModule, self)._do_logout(req)

        req.redirect(req.abs_href() + '/')

    def sentinel(self):
        return SentinelAuthenticator(self.login_url, self.app_id, self.service_url, self.service_username, self.service_password)

    sentinel = property(sentinel)
