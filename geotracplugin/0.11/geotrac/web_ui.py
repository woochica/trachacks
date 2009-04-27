import geopy

from genshi.builder import tag
from genshi.filters import Transformer
from genshi.template import TemplateLoader
from geotrac.ticket import GeolocationException
from geotrac.ticket import GeoTrac
from ticketsidebarprovider import ITicketSidebarProvider
from trac.config import BoolOption, Option
from trac.core import *
from trac.ticket import Ticket
from trac.web.api import IRequestFilter
from trac.web.api import ITemplateStreamFilter


class IssueMap(Component):
    """add a map to the ticket locations"""

    implements(ITicketSidebarProvider, ITemplateStreamFilter)

    wms_url = Option('geo', 'wms_url', 
                     'http://maps.opengeo.org/geoserver/gwc/service/wms',
                     "URL for the WMS")
    
    inject_map = BoolOption('geo', 'sidebar', 'true',
                            "whether to inject the map into the HTML")


    ### methods for ITicketSidebarProvider

    def enabled(self, req, ticket):
        if not self.inject_map:
            return False
        return self.has_location(ticket, req)

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
        if filename == 'ticket.html' and self.has_location(data['ticket'], req):
            stream |= Transformer('//head').append(tag.script('', src="http://www.openlayers.org/api/OpenLayers.js"))
            locations = [ {'geolat': req.environ['geolat'],
                           'geolon': req.environ['geolon'], }]

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

    def has_location(self, ticket, req=None):
        """should the map be shown?"""
        
        if not self.env.is_component_enabled(GeoTrac):
            return False
        geotrac = self.env.components[GeoTrac]

        # try to get the latitude and longitude from the request environ
        if req is not None:            
            lat = req.environ.get('geolat')
            lon = req.environ.get('geolon')
            if lat is not None and lon is not None:
                return True


        # geolocate the issue
        try:
            address, (lat, lon) = geotrac.locate_ticket(ticket)
        except GeolocationException:
            return False

        # cache the location on the request
        req.environ['geolat'] = lat
        req.environ['geolon'] = lon

        return True


    def mapscript(self, **data):
        """JS map for issues"""
        if not hasattr(self, 'loader'):
            from pkg_resources import resource_filename
            templates_dir = resource_filename(__name__, 'templates')
            self.loader = TemplateLoader(templates_dir,
                                         auto_reload=True)
        
        template = self.loader.load('mapscript.html')
        return template.generate(**data)


