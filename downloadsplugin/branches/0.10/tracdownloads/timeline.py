# -*- coding: utf-8 -*-

import time

from trac.core import *
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.util import Markup

from trac.Timeline import ITimelineEventProvider

from tracdownloads.api import *

class DownloadsTimeline(Component):
    """
        The timeline module implements timeline events when new downloads are
        inserted.
    """
    implements(ITimelineEventProvider)

    # ITimelineEventProvider

    def get_timeline_events(self, req, start, stop, filters):
        self.log.debug("start: %s, stop: %s, filters: %s" % (start, stop,
          filters))
        if 'downloads' in filters:
            # Create database context
            db = self.env.get_db_cnx()
            cursor = db.cursor()

            # Get API component.
            api = self.env[DownloadsApi]

            format = req.args.get('format')
            self.log.debug("format: %s" % (format))

            # Get message events
            for download in api.get_new_downloads(req, cursor, start, stop):
                kind = 'newticket'

                title = Markup("New download <em>%s</em> created by %s" %
                  (download['file'], download['author']))
                time = download['time']
                author = download['author']

                if format == 'rss':
                    href = req.abs_href.downloads(download['id'])
                    message = wiki_to_html(download['description'], self.env,
                      req)
                else:
                    href = req.href.downloads(download['id'])
                    message = wiki_to_oneliner(download['description'], self.env)

                yield kind, href, title, time, author, message

    def get_timeline_filters(self, req):
        if req.perm.has_permission('DOWNLOADS_VIEW'):
            yield ('downloads', 'Downloads changes')
