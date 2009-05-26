from genshi.filters import Transformer
from geoticket.ticket import GeoTicket
from geoticket.utils import get_column
from trac.config import BoolOption
from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import Chrome

class GeospatialQuery(Component):
    """query based on geographic data"""

    implements(ITemplateStreamFilter, IRequestFilter)

    inject_query = BoolOption('geo', 'inject_query', 'true',
                              "whether to inject the geo query fieldset into the query.html template")

    def query_by_radius(self, lat, lon, radius):
        """
        return tickets within a given radius 
        [radius in m, 
        see 
        http://postgis.refractions.net/documentation/manual-1.3/ch06.html#id2577138
        ]
        """

        # Distance functions:  see
        # * http://postgis.refractions.net/pipermail/postgis-users/2006-January/010534.html
        # * ST_DISTANCE : http://publib.boulder.ibm.com/infocenter/db2luw/v9/index.jsp?topic=/com.ibm.db2.udb.spatial.doc/rsbp4047.html
        # * http://postgis.refractions.net/documentation/manual-1.3/ch06.html#id2574404
        # * http://postgis.refractions.net/documentation/manual-1.3/ch06.html#distance_spheroid
        # * http://www.movable-type.co.uk/scripts/latlong.html#ellipsoid
        # * http://oss.openplans.org/MobileGeoTrac/ticket/54#comment:12
        
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
        
        return (template, data, content_type)

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """
        return handler


        
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

        if self.inject_query:
            chrome = Chrome(self.env)
            template = chrome.load_template('geoquery.html')
            stream |= Transformer("//fieldset[@id='columns']").after(template.generate())

        return stream

    
