import geopy

from genshi.builder import tag
from genshi.filters import Transformer
from genshi.template import TemplateLoader
from geotrac.ticket import GeoTrac
from ticketsidebarprovider import ITicketSidebarProvider
from trac.config import Option
from trac.core import *
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
            try:
                address, (lat, lon) = geotrac.geolocate(ticket['location'])
            except ValueError:
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
            data = { 'geolat': req.environ['geolat'],
                     'geolon': req.environ['geolon'],
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
