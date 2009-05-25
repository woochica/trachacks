from geoticket.ticket import GeoTicket
from geoticket.utils import get_column
from trac.core import *
from trac.web.api import ITemplateStreamFilter
trac.web.chrome import Chrome

# template loader
templates_dir = resource_filename(__name__, 'templates')
loader = TemplateLoader(templates_dir,
                        auto_reload=True)


class GeospatialQuery(Component):
    """query based on geographic data"""

    implements(ITemplateStreamFilter)

    def query_by_radius(self, lat, lon, radius):
        """
        return tickets within a given radius
        """
        # see http://postgis.refractions.net/pipermail/postgis-users/2006-January/010534.html
        # XXX units of radius?
        query_str = "ST_DISTANCE(st_pointfromtext('POINT(' || geo_lng || ' ' || geo_lat || ')'), ST_PointFromText('POINT(%s %s)')) < %s" % (lon, lat, radius)

        return get_column('ticket_location', 'ticket', where=query_str)
        
    def query_by_polyon(self, lat, lon, polygon_id):
        pass
        # XXX stub

    def geoticket(self):
        if not hasattr(self, '_geoticket'):
            assert self.env.is_component_enabled(GeoTicket)
            geoticket = self.env.components[GeoTicket]
            assert geoticket.postgis_enabled()
            self._geoticket = geoticket
        return self._geoticket
        
    ### method for ITemplateStreamFilter:
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
        self.geoticket()

        chrome = Chrome(self.env)
#        chrome.load_template()


        return stream

    
