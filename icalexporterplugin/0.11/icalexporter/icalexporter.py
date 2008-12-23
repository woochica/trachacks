"""
plugin fro Trac 0.11 to transform the provided RSS feeds
into iCalendar output
"""

import re

from ical import iCal

from trac.core import *
from trac.util.translation import _
from trac.web import IRequestFilter
from trac.web import IRequestHandler
from trac.web.chrome import add_link

class iCalExporterPlugin(Component):
    implements(IRequestHandler, IRequestFilter) 

    # paths: iCalendar path -> RSS feed path
    ics_paths = { u'/timeline/ics': u'/timeline?ticket=on&changeset=on&milestone=on&wiki=on&max=50&daysback=90&format=rss',
                  u'/ticket/([0-9]+)/ics': r'/ticket/\1?format=rss',
                  u'/log(.*)/ics': r'/log\1?limit=100&mode=stop_on_copy&format=rss',
                  u'/report(.*)/ics': r'/report\1?format=rss',
                  u'/query/ics': r'/query?format=rss'
                  }

    ### methods for IRequestHandler

    def match_request(self, req):
        """Return whether the handler wants to process the given request.
        This should be true if the URL is something like iCal
        """
        return False

    def process_request(self, req):
        """Process the request. For ClearSilver, return a (template_name,
        content_type) tuple, where `template` is the ClearSilver template to use
        (either a `neo_cs.CS` object, or the file name of the template), and
        `content_type` is the MIME type of the content. For Genshi, return a
        (template_name, data, content_type) tuple, where `data` is a dictionary
        of substitutions for the template.

        For both templating systems, "text/html" is assumed if `content_type` is
        `None`.

        Note that if template processing should not occur, this method can
        simply send the response itself and not return anything.
        """

        for path, sub in self.ics_paths.items():
            if re.match(path, req.path_info):
                filename = req.path_info.strip('/').replace('/', '.')
                rss = re.sub(path, sub, req.path_info)
                rss = req.base_url + rss
                break
        else:
            return

        # return the rss feed        
        req.send_response(200)
        req.send_header('Content-Type', 'text/calendar;charset=utf-8')
        req.send_header('Content-Disposition', 'attachment; filename=%s' % filename)
        req.end_headers()
        calendar = iCal(req.write)
        calendar.from_rss(rss)

    ### methods for IRequestFilter

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """
        if req.path_info == u'/roadmap/ics':
            req.args['format'] = 'ics'

        for path in self.ics_paths:
            if re.match(path, req.path_info):
                return self

        return handler

    # for ClearSilver templates
    def post_process_request(self, req, template, content_type):
        """Do any post-processing the request might need; typically adding
        values to req.hdf, or changing template or mime type.
        
        Always returns a tuple of (template, content_type), even if
        unchanged.

        (for 0.10 compatibility; only used together with ClearSilver templates)
        """

        # XXX not sure if this needs fixing;  
        # do i care about compatability?
        return (template, content_type)

    # for Genshi templates
    def post_process_request(self, req, template, data, content_type):
        """Do any post-processing the request might need; typically adding
        values to the template `data` dictionary, or changing template or
        mime type.
        
        `data` may be update in place.

        Always returns a tuple of (template, data, content_type), even if
        unchanged.

        (Since 0.11 - not yet stabilized)
        """

        for link in req.chrome.get('links', {}).get('alternate', ()):
            if link['class'] == 'rss':
                icshref = req.href(req.path_info, 'ics')
                add_link(req, 'alternate', icshref, _('iCalendar'),
                         'text/calendar', 'ics')            

        return (template, data, content_type)

