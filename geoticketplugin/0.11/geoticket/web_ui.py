import geopy
import simplejson

from genshi.builder import tag
from genshi.builder import Markup
from genshi.filters import Transformer
from genshi.template import TemplateLoader
from geoticket.ticket import GeolocationException
from geoticket.ticket import GeoTicket
from pkg_resources import resource_filename
from ticketsidebarprovider import ITicketSidebarProvider
from trac.config import BoolOption
from trac.config import IntOption
from trac.config import Option
from trac.core import *
from trac.ticket import Ticket
from trac.ticket.query import Query
from trac.web.api import IRequestFilter
from trac.web.api import IRequestHandler
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_script
from trac.web.chrome import add_warning, add_notice
from trac.web.chrome import INavigationContributor
from trac.web.chrome import ITemplateProvider


# template loader
templates_dir = resource_filename(__name__, 'templates')
loader = TemplateLoader(templates_dir,
                        auto_reload=True)

class GeoNotifications(Component):
    """TTW notifications for geolocation"""

    implements(IRequestFilter)

    ### methods for IRequestFilter

    def post_process_request(self, req, template, data, content_type):
        """Do any post-processing the request might need; typically adding
        values to the template `data` dictionary, or changing template or
        mime type.
        
        `data` may be update in place.

        Always returns a tuple of (template, data, content_type), even if
        unchanged.

        Note that `template`, `data`, `content_type` will be `None` if:
         - called when processing an error page
         - the default request handler did not return any result

        (Since 0.11)
        """

        if template == 'ticket.html':
            if self.env.is_component_enabled(GeoTicket):
                geoticket = self.env.components[GeoTicket]
                ticket = data['ticket']
                message = req.session.pop('geolocation_error', None)
                if message:
                    add_warning(req, Markup(message))

        return (template, data, content_type)


    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """
        return handler


class IssueMap(Component):
    """add a map to the ticket locations"""

    implements(ITicketSidebarProvider, ITemplateStreamFilter)

    inject_map = BoolOption('geo', 'inject_map', 'true',
                            "whether to inject the map into the HTML")


    ### methods for ITicketSidebarProvider

    def enabled(self, req, ticket):
        return self.inject_map

    def content(self, req, ticket):
        return tag.div('', **dict(id="map", style="width: 600px; height: 300px"))


    ### method for ITemplateStreamFilter
    ### Filter a Genshi event stream prior to rendering.

    def filter_stream(self, req, method, filename, stream, data):
        """Return a filtered Genshi event stream, or the original unfiltered
        stream if no match.

        `req` is the current request object, `method` is the Genshi render
        method (xml, xhtml or text), `filename` is the filename of the template
        to be rendered, `stream` is the event stream and `data` is the data for
        the current template.

        See the Genshi documentation for more information.
        """

        # get the GeoTicket component
        if not self.env.is_component_enabled(GeoTicket):
            return stream
        geoticket = self.env.components[GeoTicket]

        # filter for tickets
        if filename == 'ticket.html':
            if data['locations']:
                stream |= Transformer('//head').append(self.load_map(data['locations']))


        # filter for queries - add the located tickets to a map
        if (filename == 'query.html' or filename == 'report_view.html') and data['locations']:

            stream |= Transformer('//head').append(self.load_map(data['locations']))
            if self.inject_map:
                stream |= Transformer("//div[@id='content']").after(self.content(None, None))

                
        return stream

    ### internal methods

    def load_map(self, locations):
        """JS map for issues"""

        script = """$(document).ready(function() {
      var locations = %s;
      if (locations.length) {
         map_locations(locations);
      }
      
      })""" % (simplejson.dumps(locations))
        return tag.script(Markup(script), **{'type': 'text/javascript'})


class MapDashboard(Component):

    implements(IRequestHandler, INavigationContributor)

    ### configuration options
    openlayers_url = Option('geo', 'openlayers_url', 
                            'http://openlayers.org/api/2.8-rc2/OpenLayers.js',
                            "URL of OpenLayers JS to use")
    dashboard_tickets = IntOption('geo', 'dashboard_tickets', '6',
                                  "number of tickets to display on the dashboard map")

    ### methods for IRequestHandler

    """Extension point interface for request handlers."""

    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        return req.path_info.strip('/') == 'map'

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

        # get the GeoTicket component
        assert self.env.is_component_enabled(GeoTicket)
        geoticket = self.env.components[GeoTicket]
        query_string = 'location!=&status!=closed'
        query = Query.from_string(self.env, query_string)
        results = query.execute(req)
        locations = []
        tickets = []
        for result in results:
            ticket = Ticket(self.env, result['id'])
            try:
                
                address, (lat, lon) = geoticket.locate_ticket(ticket)
                content = '<a href="%s">%s</a>' % (req.href('ticket', ticket.id), ticket['summary'])
                locations.append({'latitude': lat,
                                  'longitude': lon,
                                  'content': Markup(content)})
                tickets.append(ticket)
            except GeolocationException:
                continue

        tickets.sort(key=lambda x: x.time_changed, reverse=True)
        n_tickets = len(tickets)
        tickets = tickets[:self.dashboard_tickets]
        add_script(req, 'common/js/query.js')
        data = dict(locations=Markup(simplejson.dumps(locations)), 
                    tickets=tickets,
                    n_tickets=n_tickets,
                    query_string=query_string,
                    openlayers_url=self.openlayers_url)
        return ('mapdashboard.html', data, 'text/html')

    ### methods for INavigationContributor

    """Extension point interface for components that contribute items to the
    navigation.
    """

    def get_active_navigation_item(self, req):
        """This method is only called for the `IRequestHandler` processing the
        request.
        
        It should return the name of the navigation item that should be
        highlighted as active/current.
        """
        return 'map'

    def get_navigation_items(self, req):
        """Should return an iterable object over the list of navigation items to
        add, each being a tuple in the form (category, name, text).
        """
        yield ('mainnav', 'map', tag.a('Map', href=req.href.map(), accesskey='M'))
