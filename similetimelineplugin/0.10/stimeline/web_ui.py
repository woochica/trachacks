# SimileTimeline module
# Copyright 2006 Noah Kantrowitz

from trac.core import *
from trac.web.chrome import ITemplateProvider, INavigationContributor, add_link, add_script, add_stylesheet
from trac.web.api import IRequestHandler
from trac.util.datefmt import format_date, format_time, http_date
from trac.util.html import html, Markup
from trac.util.text import to_unicode
from trac.Timeline import TimelineModule
import time, re

def add_abs_script(req, filename, mimetype='text/javascript'):
    """Add a reference to an external javascript file to the template."""
    idx = 0
    while True:
        js = req.hdf.get('chrome.scripts.%i.href' % idx)
        if not js:
            break
        if js == filename: # already added
            return
        idx += 1
    req.hdf['chrome.scripts.%i' % idx] = {'href': filename, 'type': mimetype}

class SimileTimelineModule(Component):
    
    implements(ITemplateProvider, IRequestHandler, INavigationContributor)
    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/stimeline')
        
    def process_request(self, req):
        req.perm.assert_permission('TIMELINE_VIEW')

        format = req.args.get('format')
        maxrows = int(req.args.get('max', 0))

        # Parse the from date and adjust the timestamp to the last second of
        # the day
        t = time.localtime()
        if req.args.has_key('from'):
            try:
                t = time.strptime(req.args.get('from'), '%x')
            except:
                pass

        fromdate = time.mktime((t[0], t[1], t[2], 23, 59, 59, t[6], t[7], t[8]))
        try:
            daysback = max(0, int(req.args.get('daysback', '')))
        except ValueError:
            daysback = TimelineModule(self.env).default_daysback
        req.hdf['timeline.from'] = format_date(fromdate)
        req.hdf['timeline.daysback'] = daysback

        available_filters = []
        for event_provider in TimelineModule(self.env).event_providers:
            available_filters += event_provider.get_timeline_filters(req)

        filters = []
        # check the request or session for enabled filters, or use default
        for test in (lambda f: req.args.has_key(f[0]),
                     lambda f: req.session.get('timeline.filter.%s' % f[0], '')\
                               == '1',
                     lambda f: len(f) == 2 or f[2]):
            if filters:
                break
            filters = [f[0] for f in available_filters if test(f)]

        # save the results of submitting the timeline form to the session
        if req.args.has_key('update'):
            for filter in available_filters:
                key = 'timeline.filter.%s' % filter[0]
                if req.args.has_key(filter[0]):
                    req.session[key] = '1'
                elif req.session.has_key(key):
                    del req.session[key]

        stop = fromdate
        start = stop - (daysback + 1) * 86400

        events = []
        for event_provider in TimelineModule(self.env).event_providers:
            try:
                events += event_provider.get_timeline_events(req, start, stop,
                                                             filters)
            except Exception, e: # cope with a failure of that provider
                self._provider_failure(e, req, event_provider, filters,
                                       [f[0] for f in available_filters])

        events.sort(lambda x,y: cmp(y[3], x[3]))
        if maxrows and len(events) > maxrows:
            del events[maxrows:]

        req.hdf['title'] = 'Timeline'

        # Get the email addresses of all known users
        email_map = {}
        for username, name, email in self.env.get_known_users():
            if email:
                email_map[username] = email

        idx = 0
        for kind, href, title, date, author, message in events:
            event = {'kind': kind, 'title': re.sub(r'<[^>]*>','',unicode(title)), 'href': href,
                     'author': author or 'anonymous',
                     'date': format_date(date, '%m/%d/%Y'),
                     'time': format_time(date, '%H:%M'),
                     'message': message.replace('&hellip;','...'),
                     'icon': req.href.chrome('common',kind+'.png')}

            if format == 'rss':
                # Strip/escape HTML markup
                if isinstance(title, Markup):
                    title = title.plaintext(keeplinebreaks=False)
                event['title'] = title
                event['message'] = to_unicode(message)

                if author:
                    # For RSS, author must be an email address
                    if author.find('@') != -1:
                        event['author.email'] = author
                    elif email_map.has_key(author):
                        event['author.email'] = email_map[author]
                event['date'] = http_date(date)

            req.hdf['timeline.events.%s' % idx] = event
            idx += 1

        if format == 'rss':
            return 'timeline_rss.cs', 'application/rss+xml'
        if format == 'xml':
            return 'stimeline_xml.cs', 'application/xml'

        add_stylesheet(req, 'common/css/timeline.css')
        rss_href = req.href.timeline([(f, 'on') for f in filters],
                                     daysback=90, max=50, format='rss')
        add_link(req, 'alternate', rss_href, 'RSS Feed', 'application/rss+xml',
                 'rss')
        for idx,fltr in enumerate(available_filters):
            req.hdf['timeline.filters.%d' % idx] = {'name': fltr[0],
                'label': fltr[1], 'enabled': int(fltr[0] in filters)}

        ## NEW LINES
        add_script(req, 'stimeline/js/simile/timeline-api.js')
        #add_abs_script(req, "http://simile.mit.edu/timeline/api/timeline-api.js")
        add_script(req, 'stimeline/js/simile.js')
        xml_args = {'daysback': daysback,
                    'from': time.strftime('%x',time.localtime(fromdate)),
                    'format': 'xml',
                   }
        xml_args.update(dict([(f, 'on') for f in filters]))
        
        xml_href = req.href.stimeline(**xml_args)
        req.hdf['stimeline.xml_href'] = Markup(xml_href)
        req.hdf['stimeline.href'] = req.href.stimeline()

        return 'stimeline.cs', None

    def _provider_failure(self, exc, req, ep, current_filters, all_filters):
        """Raise a TracError exception explaining the failure of a provider.

        At the same time, the message will contain a link to the timeline
        without the filters corresponding to the guilty event provider `ep`.
        """
        ep_name, exc_name = [i.__class__.__name__ for i in (ep, exc)]
        guilty_filters = [f[0] for f in ep.get_timeline_filters(req)]
        guilty_kinds = [f[1] for f in ep.get_timeline_filters(req)]
        other_filters = [f for f in current_filters if not f in guilty_filters]
        if not other_filters:
            other_filters = [f for f in all_filters if not f in guilty_filters]
        args = [(a, req.args.get(a)) for a in ('from', 'format', 'max',
                                               'daysback')]
        href = req.href.timeline(args+[(f, 'on') for f in other_filters])
        raise TracError(Markup(
            '%s  event provider (<tt>%s</tt>) failed:<br /><br />'
            '%s: %s'
            '<p>You may want to see the other kind of events from the '
            '<a href="%s">Timeline</a></p>', 
            ", ".join(guilty_kinds), ep_name, exc_name, to_unicode(exc), href))
    
    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
        
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('stimeline', resource_filename(__name__, 'htdocs'))]
        
       
    # INavigationContributer methods
    def get_active_navigation_item(self, req):
        return 'stimeline'

    def get_navigation_items(self, req):
        if req.perm.has_permission('TIMELINE_VIEW'):
            yield ('mainnav', 'stimeline', html.A('Simile Timeline', href=req.href.stimeline()))
