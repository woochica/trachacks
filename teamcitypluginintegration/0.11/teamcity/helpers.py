import socket
import urllib2
import urllib
from datetime import datetime, tzinfo, timedelta

from lxml import etree

class GMT0(tzinfo):
	"""Represent GMT+0 timezone."""
	def utcoffset(self,dt):
		return timedelta(0)

	def dst(self,dt):
		return timedelta(0)
	
	def tzname(self,dt):
		return "GMT +0"

def get_options(config):
	options = dict([
		('base_url', config.get('teamcity','base_url')),
		('username', config.get('teamcity','username')),
		('password', config.get('teamcity','password')),
		('limit', config.getint('teamcity','limit')),
		('cache_dir', config.get('teamcity','cache_dir')),
	])
	options['builds'] = config.getlist('teamcity','builds') # FIXME!
	#options['projects'] = {}
	#tc = TeamCityQuery(options)
	#projects =  config.getlist('teamcity','projects')
	#for p in projects:
#		url = '%s/httpAuth/app/rest/projects/id:%s' % (options['base_url'],p)
#		xml_data = tc.xml_query(url)
#		options['projects'][p] = {
#			'name': xml_data.xpath('/project/@name')[0],
#			'builds': [],
#		}
#		for build_tag in xml_data.xpath('/project/buildTypes/buildType'):
#			if build_tag.attrib['id'] not in options['builds']: continue
#			options['projects'][p]['builds'].append({
#				'id': build_tag.attrib['id'],
#				'name': build_tag.attrib['name'],
#			})
	return options

class TeamCityError(Exception): pass


class TeamCityQuery(object):
	"""Makes http query to Teamcity server."""

	def __init__(self, options):
		self.options = options

	def http_query(self,url,auth=True,data=None,headers={}):
		if auth: #if we need for authentication, use login and pass from options
			passmgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
			passmgr.add_password(None,self.options['base_url'],
								 self.options['username'],
								 self.options['password'])
			authhandler = urllib2.HTTPBasicAuthHandler(passmgr)
			opener = urllib2.build_opener(authhandler)
			urllib2.install_opener(opener)
		timeout = socket.getdefaulttimeout()
		socket.setdefaulttimeout(3)
		if data:
			data = urllib.urlencode(data)
		try:
			request = urllib2.Request(url,data,headers)
			response = urllib2.urlopen(request)
		except Exception,e:
			raise TeamCityError(e)
		finally:
			socket.setdefaulttimeout(timeout)
		return response

	def xml_query(self,url,auth=True):
		response = self.http_query(url,auth)
		xml_data = None
		try:
			xml_data = etree.fromstring(response.read())
		except Exception, e:
			raise TeamCityError(e)
		return xml_data
