import trac
from trac.core import *
from trac.util.html import html
from trac.web import IRequestHandler
from trac.web.api import IRequestFilter
from trac.web.chrome import INavigationContributor
from trac.perm import IPermissionRequestor, IPermissionPolicy
import trac.wiki
import trac.wiki.api


class MyPagePlugin(Component):
	trac.core.implements(IRequestHandler, IRequestFilter)

	# IRequestFilter methods
	def pre_process_request(self, req, handler):
		root = self.config.get('userpage', 'root')
		if req.path_info.startswith(root):
			self.real_handler = handler
			return self
		return handler


	def post_process_request(self, req, template, content_type):
		return (template, content_type)


	# IRequestHandler methods
	def match_request(self, req):
		root = self.config.get('userpage', 'root')
		if req.path_info.startswith(root):
			return True
		return False


	def process_request(self, req):
		root = self.config.get('userpage', 'root')
		rpath = req.path_info[len(root):]
		elements = rpath.split('/')

		if elements[0] == req.authname:
			# If it's your own page, then render without further analysis
			return self.real_handler.process_request(req)

		if self.config.has_option('userpage', 'default'):
			mode = self.config.get('userpage', 'default')
		else:
			mode = 'public'


		if len(elements) > 1 and elements[1] in ('public', 'private'):
			mode = elements[1]

		if req.perm.has_permission('TRAC_ADMIN'):
			mode = 'public'

		if mode == 'public':
			return self.real_handler.process_request(req)
		else:
			return self.noaccess(req)

		
	# public methods
	def noaccess(self, req):
		wiki = trac.wiki.api.WikiSystem(self.env)
		error = self.config.get('userpage', 'error')
		req.redirect(req.href.wiki(error))
		#req.send_response(200)
		#req.send_header('Content-type', 'text/html')
		#req.end_headers()
		#req.write(wiki.format_page_name(error))
		return

		return self._render_view(trac.wiki.model.WikiPage(self.env, error))
		req.send_response(200)
		req.send_header('Content-type', 'text/html')
		req.end_headers()
		req.write(trac.wiki.wiki_to_html('no', self.env, req))
		return

		if self.config.has_option('mypage', 'url_prefix'):
			prefix = self.config.get('mypage', 'url_prefix')
			url = prefix + url
		req.send_response(307)
		req.send_header('Location', url)
		req.end_headers()
		return
