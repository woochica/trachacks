import trac
from trac.core import *
from trac.util.html import html
from trac.web import IRequestHandler
from trac.web.api import IRequestFilter
from trac.web.chrome import INavigationContributor
from trac.perm import IPermissionRequestor, IPermissionPolicy


class MyPagePlugin(Component):
	trac.core.implements(INavigationContributor, IRequestHandler, IPermissionRequestor)

	# INavigationContributor methods
	def get_active_navigation_item(self, req):
		return 'mypage'

	def get_navigation_items(self, req):
		if req.perm.has_permission('MYPAGE_VIEW'):
			yield ('mainnav', 'mypage', html.A('My Page', href=req.href.me()))


	# IPermissionRequestor methods
	def get_permission_actions(self):
		yield 'MYPAGE_VIEW'


	# IRequestHandler methods
	def match_request(self, req):
		url = self.mypage_url(req)
		self.log.debug('match_request: url = %s' % url)
		self.log.debug('match_request: req = %s' % req.path_info)
		if req.path_info == '/me':
			return True
		return False

	def process_request(self, req):
		url = self.mypage_url(req)
		self.log.debug('process_request: %s' % url)
		if req.path_info == '/me':
			req.send_response(307)
			req.send_header('Location', url)
			req.end_headers()
			return


	# public methods
	def mypage_url(self, req):
		url = self.config.get('mypage', 'url')
		if '%' in url:
			url = url % req.authname
		return url
