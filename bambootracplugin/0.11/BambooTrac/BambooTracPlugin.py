# -*- coding: utf-8 -*-
"""
A plugin to display bamboo results in the timeline and provide a nav-link
"""

import time
import calendar
import feedparser
import urlparse
import urllib2
from datetime import datetime
from trac.core import *
from trac.config import Option, BoolOption
from trac.util import Markup, format_datetime
from trac.web.chrome import ITemplateProvider, add_stylesheet
try:
    from trac.timeline.api import ITimelineEventProvider
except ImportError:
    from trac.Timeline import ITimelineEventProvider

class BambooTracPlugin(Component):
    implements(ITimelineEventProvider, ITemplateProvider)

    feed_url = Option('bamboo', 'feed_url', 'http://localhost/bamboo/rss/createAllBuildsRssFeed.action?feedType=rssAll&os_username=user&os_password=pass',
                      'The url of the bamboo rss feed containing the build ' +
                      'statuses. This must be an absolute url.' +
					  'Note that you may need to add &os_username=user&os_password=pass or &os_authType=basic' +
					  'depending on the type of authentication you want to use')
    username = Option('bamboo', 'username', '',
                      'The username to use to access bamboo if using basic authentication')
    password = Option('bamboo', 'password', '',
                      'The password to use to access bamboo if using basic authentication')
    nav_url  = Option('bamboo', 'main_page', 'http://localhost/bamboo/',
                      'The url of the bamboo main page to which the trac nav ' +
                      'entry should link; if empty, no entry is created in ' +
                      'the nav bar. This may be a relative url.')
    disp_tab = BoolOption('bamboo', 'display_in_new_tab', 'false',
                          'Open bamboo page in new tab/window')

    def __init__(self):
        pwdMgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        pwdMgr.add_password(None, urlparse.urlsplit(self.feed_url)[1], self.username, self.password)

        self.bAuth = urllib2.HTTPBasicAuthHandler(pwdMgr)
        self.dAuth = urllib2.HTTPDigestAuthHandler(pwdMgr)

        self.url_opener = urllib2.build_opener(self.bAuth, self.dAuth)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'builds'

    def get_navigation_items(self, req):
        if self.nav_url:
            yield 'mainnav', 'builds', Markup('<a href="%s"%s>Builds</a>' % \
                        (self.nav_url, self.disp_tab and ' target="bamboo"' or ''))

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [self.env.get_templates_dir(),
                self.config.get('trac', 'templates_dir')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('BambooTrac', resource_filename(__name__, 'htdocs'))]

    # ITimelineEventProvider methods

    def get_timeline_filters(self, req):
        if req.perm.has_permission('CHANGESET_VIEW'):
            yield ('build', 'Bamboo Builds')

    def get_timeline_events(self, req, start, stop, filters):
        if isinstance(start, datetime): # Trac>=0.11
                from trac.util.datefmt import to_timestamp
                start = to_timestamp(start)
                stop = to_timestamp(stop)

        if 'build' in filters:
            add_stylesheet(req, 'BambooTrac/bambootrac.css')

            feed = feedparser.parse(self.feed_url, handlers=[self.bAuth, self.dAuth])

            for entry in feed.entries:

                # check time range
                completed = calendar.timegm(entry.date_parsed)

                # create timeline entry
                if entry.title.find('SUCCESS') >= 0:
                    message = 'Build finished successfully'
                    kind = 'bamboo-successful'
                else:
                    message = 'Build failed'
                    kind = 'bamboo-failed'

                fulltitle = entry.title.split(":")
                newtitle = fulltitle[0]
				
                href = entry.link
                title = entry.title

                comment = message + ' at ' + format_datetime(completed)

                yield kind, href, newtitle, completed, None, comment
