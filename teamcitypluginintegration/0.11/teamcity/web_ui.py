import os
import re
import urlparse
import urllib2
from datetime import datetime

import pkg_resources
from lxml import etree
from trac.core import *
from trac.util.html import html
from trac.web import HTTPNotFound, HTTPBadGateway, HTTPForbidden
from trac.web.main import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet, add_javascript

from helpers import get_options, TeamCityQuery, TeamCityError


class TeamCityChrome(Component):
	"""Provides plugin templates and static resources."""
	implements(ITemplateProvider)

	# ITemplatesProvider methods
	def get_htdocs_dirs(self):
		"""Return the directories containing static resources."""
		return [('teamcity', pkg_resources.resource_filename(__name__, 'htdocs'))]

	def get_templates_dirs(self):
		return [pkg_resources.resource_filename(__name__, 'templates')]


class TeamCityLogLoader(Component):
	"""Loads build log from teamcity by request and localy caches it."""
	implements(IRequestHandler)

	def __init__(self):
		self.options = get_options(self.config)
		self.msg_cache_dir = self.options['cache_dir'] or '/tmp/teamcity_cache'
		if not os.path.exists(self.msg_cache_dir):
			try:
				os.mkdir(self.msg_cache_dir)
			except OSError,e:
				self.log.error("Can't create cache_dir: %s" % e)

	# IRequestHandler methods
	def match_request(self,req):
		"""Only 'builds/download/{build_id} urls are handled."""
		return re.match(r'/builds/download/(\d+)$', req.path_info)

	def process_request(self,req):
		"""Handles build log downloading."""
		build_id = re.match(r'/builds/download/(\d+)$', req.path_info).groups()[0]
		log = self._get_build_message(build_id)
		req.send_header('Content-Type','text/plain')
		req.send_header('Content-Length',len(log))
		req.end_headers()
		req.write(log)

	# custom private methods to load/cache build log
	def _get_build_message(self,build_id):
		"""Returns full build log.

		This is a wrapper method that tries to load build log from cache or, 
		if this failed, to load build log from teamcity server and cache the result.
		Arguments:
		build_id - buildId in the teamcity database
		"""
		msg_file = os.path.join(self.msg_cache_dir,'build_%s.msg' % build_id)
		try:
			#loading log from cache
			f = open(msg_file, 'r')
			log = f.read()
		except IOError,e: 
			# Can't read build log from cache here,
			# so let's try to load it from teamcity server. 
			# Url to build log looks like this: 
			# http://ci:8111/httpAuth/downloadBuildLog.html?buildId=109
			build_url = "%s?buildId=%s" % (self.options['base_url'], build_id)
			url_obj = urlparse.urlparse(build_url)
			build_log_url = "%s://%s/%s?%s" % (url_obj.scheme,
								url_obj.netloc,
								'httpAuth/downloadBuildLog.html',
								url_obj.query
								)
			try:
				log = self._load_build_log(build_log_url)
			except Exception,e:
				log = "Can't load build log: %s" % e
				self.log.error(log)
			else: # load from teamcity server was successful
				if e.errno == 2: # cache file was not found, create new one
					self._save_build_log(msg_file, log)
		else:
			f.close()
		return log

	def _load_build_log(self,url):
		"""Loads build log from teamcity server.

		Arguments:
		url - url to load log from
		"""
		passmgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
		passmgr.add_password(None,url,self.options['username'],
							 self.options['password'])
		authhandler = urllib2.HTTPBasicAuthHandler(passmgr)
		opener = urllib2.build_opener(authhandler)
		urllib2.install_opener(opener)
		fp = urllib2.urlopen(url)
		return fp.read()

	def _save_build_log(self,msg_file, msg):
		"""Saves build log to cache.

		Arguments:
		msg_file - filename in cache dir
		msg - build log
		"""
		try:
			f = open(msg_file, 'w')
			f.write(msg)
		except IOError,e:
			self.log.error("Can't save build log to cache: %s" % e)
		else:
			f.close()


class TeamCityBuildPage(Component):
	"""Renders pages with build results."""
	implements(IRequestHandler,INavigationContributor,IPermissionRequestor)

	# IPermissionRequestor
	def get_permission_actions(self):
		actions = ['TEAMCITY_BUILD']
		return actions + [('TEAMCITY_ADMIN', actions)]

	# INavigationContributor methods
	def get_active_navigation_item(self,req):
		return 'teamcity_builds'

	def get_navigation_items(self,req):
		if req.perm.has_permission('TEAMCITY_BUILD'):
			yield 'mainnav', 'teamcity_builds', html.A('Builds', href=req.href.builds())

	#IRequestHandler methods
	def match_request(self,req):
		return re.match('/builds/?(bt\d+)?$',req.path_info)


	def process_request(self,req):
		if not req.perm.has_permission('TEAMCITY_BUILD'):
			raise HTTPForbidden('You are not allowed to view/run TC builds')
		options = get_options(self.config)
		tc = TeamCityQuery(options)
		# projects variable will collect builds result in following format:
		# {'projectId': { 
		#			'name': 'Proj1', 
		#			'btypes': [{		# it's a list of build types assigned to this project
		#					'btype_id': 'bt1',
		#					'btype_name': 'PS3 builds'
		#					'build': {
		#							'number': 5555 # teamcity number
		#							'status': 'Success',
		#							'start_date': datetime_object,
		#							'end_date': datetime_object,
		#					},]
		#			}
		# }
		projects = {}
		for build_type in options['builds']:
			# load builds xml from teamcity
			url = "%s/httpAuth/app/rest/buildTypes/id:%s/builds" %\
										(options['base_url'],build_type)
			btype_xml = tc.xml_query(url)
			if btype_xml is None:
				self.log.error("Can't load builds xml at %s" % url)
				continue
			if len(btype_xml) < 1: # there is not any builds yet
				url = '%s/httpAuth/app/rest/buildTypes/id:%s' % (options['base_url'], build_type)
				build_xml = tc.xml_query(url)
				if build_xml is None:
					continue
				proj_id = build_xml.xpath('/buildType/project/@id')[0]
				# collect here as many build info as possible and continue
				build_info = {
					'btype_id': build_type,
					'btype_name': build_xml.attrib['name'],
					'build': {
						'id': None,
						'number': None,
						'status': 'unknown',
						'end_date': 'Never',
						'duration': 'Unknown'
					}
				}
				if proj_id in projects:
					projects[proj_id]['btypes'].append(build_info)
				else: # or create new item in projects
					projects[proj_id] = {
						'name': proj_name,
						'btypes': [build_info,]
					}
				continue

			# There is at least one finished build
			last_build = btype_xml[0].attrib
			# load this build xml
			url = "%s%s" % (options['base_url'],last_build['href'])
			build_xml = tc.xml_query(url)
			if build_xml is None:
				self.log.error("Can't load build xml at %s" % url)
			proj_id = build_xml.xpath('/build/buildType/@projectId')[0]
			proj_name =  build_xml.xpath('/build/buildType/@projectName')[0]
			# Fuck! python2.5 has not support for timezones in datetime.strptime
			try:
				# datetime lacks timezone info
				start_date =  build_xml.xpath('/build/startDate/text()')[0].split('+')[0] 
				start_date = datetime.strptime(start_date, '%Y%m%dT%H%M%S')
				# datetime lacks timezone info
				end_date = build_xml.xpath('/build/finishDate/text()')[0].split('+')[0] 
				end_date = datetime.strptime(end_date, '%Y%m%dT%H%M%S')
			except IndexError: # no start_date or end_date, duration is unknown
				end_date = 'Never'
				duration = 'Unknown'
			else:
				duration = end_date - start_date
			# parse build status
			try:
				status = build_xml.xpath('/build/statusText/text()')[0].lower()
			except IndexError: # no last status yet
				status = 'unknown'
			# result build dictionary
			build_info = {
				'btype_id': build_type,
				'btype_name': build_xml.xpath('/build/buildType/@name')[0],
				'build': {
					'id': build_xml.attrib['id'],
					'number': build_xml.attrib['number'],
					'status': status,
					'end_date': end_date,
					'duration': duration
				}
			}
			# add new build to project
			if proj_id in projects:
				projects[proj_id]['btypes'].append(build_info)
			else: # or create new item in projects
				projects[proj_id] = {
					'name': proj_name,
					'btypes': [build_info,]
				}
		add_stylesheet(req,'teamcity/css/teamcity.css')
		add_javascript(req,'teamcity/js/jquery.timers-1.2.js')
		add_javascript(req,'teamcity/js/event_tracker.js')
		return 'teamcity_builds.html', {
					'projects':projects,
					'dpath':req.href('builds/download')
					}, None

class TeamCityProxy(Component):
	implements(IRequestHandler)

	def __init__(self):
		self.options = get_options(self.config)

	#IRequestHandler methods
	def match_request(self,req):
		return re.match(r'/builds/proxy(?:_trac)?(?:/.*)?$',req.path_info)

	def process_request(self,req):
		try:
			path = req.path_info.split('/builds/proxy/')[1]
		except IndexError: # no trailing slash ex.
			raise HTTPNotFound("Invalid proxy url, no trailing slash")
		t_url = "%s/httpAuth/%s?%s" % (self.options['base_url'],
							  path,req.environ['QUERY_STRING'])
		tc = TeamCityQuery(self.options)
		try:
			response = tc.http_query(t_url)
		except TeamCityError, e:
			raise HTTPBadGateway('An error occured during proxy request to %s: %s' % (t_url, e))
		req.send_response(200)
		content_type = response.headers.get('Content-Type', 'text/plain')
		req.send_header('Content-Type',content_type)
		# need to save original Content-Type header
		req.end_headers()
		req.write(response.read())


class TeamCityHistory(Component):

	implements(IRequestHandler)

	#IRequestHandler methods
	def match_request(self,req):
		return re.match(r'/builds/history/?(bt\d+)?$',req.path_info)


	def process_request(self,req):
		options = get_options(self.config)
		build_type_match =  re.match('/builds/history/(bt\d+)?$',req.path_info)
		if build_type_match is None:
			query_string =  "&".join(['buildTypeId=%s' % id for id in options['builds']])
		else:
			build_type_id = build_type_match.groups()[0]
			query_string = 'buildTypeId=%s' % build_type_id
		add_stylesheet(req, 'teamcity/css/teamcity.css')
		query_string += '&sinceDate=-%d' % options['limit']
		feed_url = "%s/feed.html?%s" % (options['base_url'], query_string)
		tc = TeamCityQuery(self.options)
		feed = TeamCityQuery.xml_query(feed_url)
		if feed is None:
			raise HTTPNotFound("Can't load feed")
		data = {'entries': []}
		for entry in feed.iterfind('{http://www.w3.org/2005/Atom}entry'):
			title = entry.find('{http://www.w3.org/2005/Atom}title').text
			link = entry.find('{http://www.w3.org/2005/Atom}link').attrib['href']
			date = entry.find('{http://www.w3.org/2005/Atom}published').text
			date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
			summary = entry.find('{http://www.w3.org/2005/Atom}summary').text
			summary =  summary.split('<a href')[0]
			build_id_match = re.search('buildId=(\d+)', link)
			if build_id_match:
				summary += "<br/><a href='%s'>Build Log</a>" % \
						req.href.builds('download', build_id_match.groups()[0])
			data['entries'].append({
					'title': title,
					'link': link,
					'date': date,
					'summary': summary,
				})
		return 'teamcity_status.html', data, None
