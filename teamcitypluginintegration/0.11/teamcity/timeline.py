import os
import re
import urlparse
from datetime import datetime

from trac.core import *
from trac.timeline import ITimelineEventProvider
from trac.web.chrome import add_stylesheet, add_javascript
from genshi.builder import tag

from helpers import GMT0, get_options, TeamCityQuery, TeamCityError

def get_build_ids(build_url):
	"""Parses url to find buildTypeId and buildId GET params.

	Arguments:
	build_url - url of the teamcity build.
	"""
	# parse build_url
	url_obj = urlparse.urlparse(build_url)
	# parse query params
	params = dict([part.split('=') for part in url_obj.query.split('&')])
	return params.get('buildId'), params.get('buildTypeId')


class TeamCityTimeline(Component):
	"""Provides timeline events and downloads build logs"""

	implements(ITimelineEventProvider)

	def __init__(self):
		self.options = get_options(self.config)

	# ITimelineEventProvider methods
	def get_timeline_filters(self, req):
		"""Returns a list of filters that this event provider supports.

		Full description here http://trac.edgewall.org/browser/trunk/trac/timeline/api.py
		"""
		yield ('build', 'TeamCity Builds')

	def get_timeline_events(self, req, start, stop, filters):
		"""Returns a list of events in the time range given by the `start` and
		`stop` parameters.

		Full description here http://trac.edgewall.org/browser/trunk/trac/timeline/api.py
		"""
		if 'build' not in filters:
			return
		# exit if there is not any buildType in options
		if not self.options.get('builds',True):
			return
		# get rss feed 
		query_string =  "&".join(['buildTypeId=%s' % id for id in self.options['builds']])
		query_string += '&sinceDate=-%d' % self.options['limit']
		feed_url = "%s/httpAuth/feed.html?%s" % (self.options['base_url'], query_string)
		tc = TeamCityQuery(self.options)
		try:
			feed = tc.xml_query(feed_url)
		except TeamCityError as e:
			self.log.error("Error while proceed TeamCity events: %s" % e)
			return
		if feed is None:
			self.log.error("Can't get teamcity feed")
			return
		add_stylesheet(req,'teamcity/css/teamcity.css')
		add_javascript(req,'teamcity/js/loadlog.js')
		# iterate over resulted xml feed
		for entry in feed.iterfind('{http://www.w3.org/2005/Atom}entry'):
			event_date = entry.find('{http://www.w3.org/2005/Atom}published').text
			event_date = datetime.strptime(event_date, '%Y-%m-%dT%H:%M:%SZ')
			event_date = event_date.replace(tzinfo=GMT0())
			if (event_date < start) or (event_date > stop): continue
			event_title = entry.find('{http://www.w3.org/2005/Atom}title').text
			event_status =  entry.find('{http://purl.org/dc/elements/1.1/}creator').text
			event_status = event_status.lower().replace(' ','_')
			# get build id
			build_url = entry.find('{http://www.w3.org/2005/Atom}link').attrib['href']
			build_id, build_type = get_build_ids(build_url)
			# get build message 
			if event_status == 'successful_build':
				msg = 'Build was successful'
			else:
				msg = 'Build failed'
			data = {
				'date': event_date,
				'status': event_status,
				'title': event_title,
				'build_url': build_url,
				'build_type': build_type,
				'build_id': build_id,
				'message': msg,
			}
			yield event_status, event_date, 'ci server', data

	def render_timeline_event(self, context, field, event):
		"""Display the title of the event in the given context.

		Full description here http://trac.edgewall.org/browser/trunk/trac/timeline/api.py
		"""
		if field == 'url':
			return context.href.builds(event[3]['build_type'])
		elif field == 'title':
			return event[3]['title']
		elif field == 'description':
			msg = tag.div('hehe',class_='hiddenlog')
#			msg = tag.div(tag.p(event[3]['message']), tag.a('View build log',class_='show_log',
#						href=context.href.builds('download', event[3]['build_id'])), msg)
			msg = tag.div(tag.a('View build log',class_='show_log',
						href=context.href.builds('download', event[3]['build_id'])), msg)
			return msg

