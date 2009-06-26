# -*- coding: utf-8 -*-
"""
A plugin to display hudson results in the timeline and provide a nav-link
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
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
try:
    from trac.timeline.api import ITimelineEventProvider
except ImportError:
    from trac.Timeline import ITimelineEventProvider

class HudsonTracPlugin(Component):
    implements(INavigationContributor, ITimelineEventProvider, ITemplateProvider)

    disp_sub = BoolOption('hudson', 'display_subprojects', 'false',
                          'Display status of subprojects in timeline too')
    feed_url = Option('hudson', 'feed_url', 'http://localhost/hudson/rssAll',
                      'The url of the hudson rss feed containing the build ' +
                      'statuses. This must be an absolute url.')
    username = Option('hudson', 'username', '',
                      'The username to use to access hudson (feed and details)')
    password = Option('hudson', 'password', '',
                      'The password to use to access hudson (feed and details)')
    nav_url  = Option('hudson', 'main_page', '/hudson/',
                      'The url of the hudson main page to which the trac nav ' +
                      'entry should link; if empty, no entry is created in ' +
                      'the nav bar. This may be a relative url.')
    disp_tab = BoolOption('hudson', 'display_in_new_tab', 'false',
                          'Open hudson page in new tab/window')
    alt_succ = BoolOption('hudson', 'alternate_success_icon', 'false',
                          'Use an alternate success icon (green ball instead ' +
                          'of blue)')
    use_desc = BoolOption('hudson', 'display_build_descriptions', 'true',
                          'Whether to display the build descriptions for ' +
                          'each build instead of the canned "Build finished ' +
                          'successfully" etc messages. You may want to ' + 
                          'disable this if it slows things down too much or ' +
                          'if you run into issues with hudson.')

    def __init__(self):
        url_parts = urlparse.urlsplit(self.feed_url)
        base_url  = url_parts.scheme + '://' + url_parts.netloc + '/'

        pwdMgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        pwdMgr.add_password(None, base_url, self.username, self.password)

        bAuth = urllib2.HTTPBasicAuthHandler(pwdMgr)
        dAuth = urllib2.HTTPDigestAuthHandler(pwdMgr)

        self.url_opener = urllib2.build_opener(bAuth, dAuth)

        self.env.log.debug("registered auth-handler for '%s', username='%s'" %
                           (base_url, self.username))

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'builds'

    def get_navigation_items(self, req):
        if self.nav_url:
            yield 'mainnav', 'builds', Markup('<a href="%s"%s>Builds</a>' % \
                        (self.nav_url, self.disp_tab and ' target="hudson"' or ''))

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [self.env.get_templates_dir(),
                self.config.get('trac', 'templates_dir')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('HudsonTrac', resource_filename(__name__, 'htdocs'))]

    # ITimelineEventProvider methods

    def get_timeline_filters(self, req):
        if req.perm.has_permission('CHANGESET_VIEW'):
            yield ('build', 'Hudson Builds')

    def get_timeline_events(self, req, start, stop, filters):
        if not 'build' in filters:
            return

        if isinstance(start, datetime): # Trac>=0.11
            from trac.util.datefmt import to_timestamp
            start = to_timestamp(start)
            stop = to_timestamp(stop)

        add_stylesheet(req, 'HudsonTrac/hudsontrac.css')

        try:
            feed = feedparser.parse(self.url_opener.open(self.feed_url))
        finally:
            self.url_opener.close()

        if getattr(feed, 'status', 0) >= 400:
            raise IOError, "Error getting feed '%s': http-status=%d" % (self.feed_url, feed.status)
        if feed.bozo:
            raise IOError, "Error getting feed '%s': %s" % (self.feed_url, feed.bozo_exception)

        for entry in feed.entries:
            # Only look at top-level entries
            if not self.disp_sub and entry.title.find(u'»') >= 0:
                continue

            # check time range
            completed = calendar.timegm(entry.updated_parsed)
            if completed > stop:
                continue
            if completed < start:
                break

            # create timeline entry
            if entry.title.find('SUCCESS') >= 0:
                message = 'Build finished successfully'
                kind = self.alt_succ and 'build-successful-alt' or 'build-successful'
            elif entry.title.find('UNSTABLE') >= 0:
                message = 'Build unstable'
                kind = 'build-unstable'
            elif entry.title.find('ABORTED') >= 0:
                message = 'Build aborted'
                kind = 'build-aborted'
            else:
                message = 'Build failed'
                kind = 'build-failed'

            href = entry.link
            title = entry.title

            if self.use_desc:
                url = href + '/api/json'
                try:
                    line = self.url_opener.open(url).readline()
                finally:
                    self.url_opener.close()
                json = eval(line.replace('false', 'False').replace('true','True').replace('null', 'None'))

                if json['description']:
                    message = unicode(json['description'], 'utf-8')

            comment = message + ' at ' + format_datetime(completed)

            yield kind, href, title, completed, None, comment

