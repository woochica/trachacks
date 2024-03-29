from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import Markup, TracError
from trac.util.text import to_unicode
import re

import xmlrpclib, pkg_resources


class BuildBotPlugin(Component):
	"""A plugin to integrate Buildbot into Trac
	"""
	implements(INavigationContributor, IRequestHandler, ITemplateProvider)

	def get_buildbot_url(self):
		url=self.config.get("buildbot", "url")
		return url.strip('/')

	def get_xmlrpc_url(self):
		return self.get_buildbot_url() + "/xmlrpc"

	def get_builder_url(self, builder_name):
		return self.get_buildbot_url() + "/builders/" + builder_name

	def get_build_url(self, builder_name, build_number):
		return ("%s/builds/%d" % (self.get_builder_url(builder_name), build_number))


	def get_server (self):
		return xmlrpclib.ServerProxy(self.get_xmlrpc_url())

	def get_active_navigation_item(self, req):
		return "buildbot"

	def get_navigation_items(self, req):
		yield 'mainnav', 'buildbot', Markup('<a href="%s">BuildBot</a>' % self.env.href.buildbot())

	# ITemplateProvider methods
	def get_templates_dirs(self):
		"""
		Return the absolute path of the directory containing the provided
		ClearSilver templates.
		"""
		return [pkg_resources.resource_filename(__name__, 'templates')]

	def get_htdocs_dirs(self):
		return [('tracbb', pkg_resources.resource_filename(__name__, 'htdocs'))]

	# IRequestHandler methods
	def match_request(self, req):
		match = re.match(r'/buildbot(/([^\/]*))?(/(\d+))?$', req.path_info)
		if match:
			if match.group(2):
				req.args['builder'] = match.group(2)
				if match.group(4):
					req.args['buildnum'] = match.group(4)
			return True
		return False



	def get_builders(self, req):
		server = None
		try:
			server = self.get_server()
			builders = server.getAllBuilders()
		except:
			raise TracError("Can't get access to buildbot at " + self.get_xmlrpc_url())
		ret = []
		for builder in builders:
			lastbuild = server.getLastBuilds(builder,1)[0]
			build = { 'name' : builder,
				'status' : server.getStatus(builder),
				'url' : req.href.buildbot(builder),
				'lastbuild' : lastbuild[1],
				'lastbuildurl' : self.get_build_url(builder, lastbuild[1])
				}
			ret.append(build)

		return ret

	def get_last_builds(self, builder):
		server = None
		builds = None
		try:
			server = self.get_server()
			builds = server.getLastBuilds(builder, 5)
		except:
			raise TracError("Can't get builder %s on url %s" % (builder, self.get_xmlrpc_url()))
		#last build first
		builds.reverse()
		ret = []
		for build in  builds:
			thisbuild = { 'status' : build[5],
				'number' : build[1],
				'url' : self.get_build_url(builder, build[1])
				}
			ret.append(thisbuild)

		return ret



	def process_request(self, req):
		if not req.args.has_key('builder'):
			req.hdf['title'] = 'BuildBot'

			req.hdf['bb.builders'] = self.get_builders(req)

			return 'tracbb_overview.cs', None
		else:
			builder = req.args['builder']
			builds = self.get_last_builds(builder)
			req.hdf['title'] = 'Builder ' + builder
			req.hdf['bb.builder'] = builder
			req.hdf['bb.builds'] = builds
			return 'tracbb_builder.cs', None
