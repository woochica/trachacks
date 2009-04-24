import geopy

from genshi.builder import tag
from genshi.filters import Transformer
from genshi.template import TemplateLoader
from geotrac.ticket import GeolocationException
from geotrac.ticket import GeoTrac
from ticketsidebarprovider import ITicketSidebarProvider
from trac.config import Option
from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.api import ITemplateStreamFilter


class SidebarMap(Component):
    """add a map to the ticket sidebar"""

    implements(ITicketSidebarProvider, ITemplateStreamFilter)

    wms_url = Option('geo', 'wms_url', 
                     'http://maps.opengeo.org/geoserver/gwc/service/wms',
                     "URL for the WMS")


    ### methods for ITicketSidebarProvider

    def enabled(self, req, ticket):
        """should the map be shown?"""
        
        if not self.env.is_component_enabled(GeoTrac):
            return False
        geotrac = self.env.components[GeoTrac]

        if not ticket['location']:
            return False

        # get the latitude and longitude from the request environ
        lat = req.environ.get('geolat')
        lon = req.environ.get('geolon')

        if lat is None or lon is None: # lat or lon could be zero

            # XXX blindly assume UTF-8
            try:
                location = ticket['location'].encode('utf-8')
            except UnicodeEncodeError:
                raise
            
            try:
                address, (lat, lon) = geotrac.geolocate(location)
            except GeolocationException:
                return False
            req.environ['geolat'] = lat
            req.environ['geolon'] = lon

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

        if filename == 'ticket.html' and self.enabled(req, data['ticket']):
            stream |= Transformer('//head').append(tag.script('', src="http://www.openlayers.org/api/OpenLayers.js"))
            locations = [ {'geolat': req.environ['geolat'],
                           'geolon': req.environ['geolon'], }]

            data = { 'locations': locations,
                     'wms_url': self.wms_url }
            stream |= Transformer('//head').append(self.mapscript(**data))
            stream |= Transformer('//body').attr('onload', 'init()')

        return stream

    def mapscript(self, **data):
        if not hasattr(self, 'loader'):
            from pkg_resources import resource_filename
            templates_dir = resource_filename(__name__, 'templates')
            self.loader = TemplateLoader(templates_dir,
                                         auto_reload=True)

        template = self.loader.load('mapscript.html')
        return template.generate(**data)


class GeoRequestFilter(Component):

    implements(IRequestFilter)

    ### methods for IRequestFilter

    """Extension point interface for components that want to filter HTTP
    requests, before and/or after they are processed by the main handler."""

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
        geotrac = self.env.components.get(GeoTrac)
        if geotrac is None:
            return template, data, content_type

        if template == 'ticket.html':
            pass
        return template, data, content_type

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """
        return handler

