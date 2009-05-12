import geopy

from pkg_resources import resource_filename

from genshi.builder import tag
from genshi.filters import Transformer
from genshi.template import TemplateLoader
from geotrac.ticket import GeolocationException
from geotrac.ticket import GeoTrac
from ticketsidebarprovider import ITicketSidebarProvider
from trac.config import BoolOption, Option
from trac.core import *
from trac.ticket import Ticket
from trac.ticket.query import Query
from trac.web.api import IRequestFilter
from trac.web.api import IRequestHandler
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_script
from trac.web.chrome import INavigationContributor
from trac.web.chrome import ITemplateProvider


# template loader
templates_dir = resource_filename(__name__, 'templates')
loader = TemplateLoader(templates_dir,
                        auto_reload=True)


class IssueMap(Component):
    """add a map to the ticket locations"""

    implements(ITicketSidebarProvider, ITemplateStreamFilter)

    wms_url = Option('geo', 'wms_url', 
                     'http://maps.opengeo.org/geoserver/gwc/service/wms',
                     "URL for the WMS")
    
    inject_map = BoolOption('geo', 'inject_map', 'true',
                            "whether to inject the map into the HTML")


    ### methods for ITicketSidebarProvider

    def enabled(self, req, ticket):
        if not self.inject_map:
            return False

        if not self.env.is_component_enabled(GeoTrac):
            return False
        geotrac = self.env.components[GeoTrac]

        # geolocate the issue
        try:
            address, (lat, lon) = geotrac.locate_ticket(ticket)
        except GeolocationException:
            return False

        return True

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

        # get the GeoTrac component
        if not self.env.is_component_enabled(GeoTrac):
            return stream
        geotrac = self.env.components[GeoTrac]

        # filter for tickets
        if filename == 'ticket.html':
            try:
                address, (geolat, geolon) = geotrac.locate_ticket(data['ticket'])
            except GeolocationException:
                return stream
            stream |= Transformer('//head').append(tag.script('', src="http://www.openlayers.org/api/OpenLayers.js"))

            locations = [ {'geolat': geolat,
                           'geolon': geolon, }]

            _data = { 'locations': locations,
                     'wms_url': self.wms_url }
            stream |= Transformer('//head').append(self.mapscript(**_data))
            stream |= Transformer('//body').attr('onload', 'init()')
            data.update(_data)
            
        # filter for queries
        if filename == 'query.html':
            
            locations = []
            for _ticket in data['tickets']:

                # TODO : instead of loading the ticket object to get the
                # location, could ensure that location is fetched with the query
                # with, say an IRequestFilter
                ticket = Ticket(self.env, _ticket['id'])
                try:
                    address, (lat, lon) = geotrac.locate_ticket(ticket)
                    locations.append({'geolat': lat, 'geolon': lon})
                except GeolocationException:
                    pass
                        
            # add the located tickets to a map
            if locations:
                _data = { 'locations': locations,
                          'wms_url': self.wms_url }
                stream |= Transformer('//head').append(tag.script('', src="http://www.openlayers.org/api/OpenLayers.js"))
                stream |= Transformer('//head').append(self.mapscript(**_data))
                stream |= Transformer('//body').attr('onload', 'init()')
                if self.inject_map:
                    stream |= Transformer("//div[@id='content']").after(self.content(None, None))

                data.update(_data)

        return stream

    ### internal methods

    def mapscript(self, **data):
        """JS map for issues"""
        template = loader.load('mapscript.html')
        return template.generate(**data)


class MapDashboard(Component):

    implements(ITemplateProvider, IRequestHandler, INavigationContributor)

    wms_url = Option('geo', 'wms_url', 
                     'http://maps.opengeo.org/geoserver/gwc/service/wms',
                     "URL for the WMS")

    ### methods for ITemplateProvider

    """Extension point interface for components that provide their own
    ClearSilver templates and accompanying static resources.
    """

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return []

    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        return [templates_dir]

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

        # get the GeoTrac component
        assert self.env.is_component_enabled(GeoTrac)
        geotrac = self.env.components[GeoTrac]

        query = Query.from_string(self.env, 'location!=')
        results = query.execute(req)

        locations = []
        for result in results:
            try:
                address, (lat, lon) = geotrac.geolocate(result.get('location'))
                locations.append({'geolat': lat,
                                  'geolon': lon})
            except GeolocationException:
                continue

        add_script(req, 'common/js/query.js')
        template = loader.load("mapscript.html")
        mapscript = template.generate(wms_url=self.wms_url, locations=locations)

        locations = []
        return ('mapdashboard.html', dict(locations=locations, mapscript=mapscript), 
                                          'text/html')

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
