import simplejson
import sys
import trac.ticket.query

from componentdependencies import IRequireComponents
from genshi.builder import tag
from genshi.builder import Markup
from genshi.filters import Transformer
from geoticket.regions import GeoRegions
from geoticket.ticket import GeolocationException
from geoticket.ticket import GeoTicket
from trac.config import BoolOption
from trac.core import *
from trac.ticket.query import Query
from trac.web.href import Href
from trac.web.api import IRequestFilter
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_script
from trac.web.chrome import add_warning
from trac.web.chrome import Chrome
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase
from tracsqlhelper import get_column

# XXX for scary magic below
original_href_call = Href.__call__
patched = False

class GeospatialQuery(Component):
    """query based on geographic data"""

    implements(ITemplateStreamFilter, IRequestFilter)

    inject_query = BoolOption('geo', 'inject_query', 'true',
                              "whether to inject the geo query fieldset into the query.html template")

    # conversion to meters
    units = { 'blocks': 80.4672,
              }

    ### internal methods

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
        
        query_str = "ST_DISTANCE_SPHERE(st_pointfromtext('POINT(' || longitude || ' ' || latitude || ')'), ST_PointFromText('POINT(%s %s)')) < %s" % (lon, lat, radius)

        tickets = get_column(self.env, 'ticket_location', 'ticket', where=query_str)
        assert tickets is not None
        return tickets
        
    def query_by_polygon(self, region):
        georegions = GeoRegions(self.env)
        return georegions.tickets_in_region(region)

    def geoticket(self):
        if not hasattr(self, '_geoticket'):
            assert self.env.is_component_enabled(GeoTicket)
            geoticket = self.env.components[GeoTicket]
            assert geoticket.postgis_enabled(), "PostGIS is not enabled and must be for GeospatialQueries to work.  Enable PostGIS on the database or disable the GeospatialQuery component."
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

        if template != 'query.html':        
            return (template, data, content_type)

        geoticket = self.geoticket()
        location = req.args.get('center_location', '').strip()
        lat = lon = None
        if location:
            try:
                location, (lat, lon) = geoticket.geolocate(location)
            except GeolocationException, e:
                add_script(req, 'geoticket/js/query_location_filler.js')
                add_warning(req, Markup(e.html()))
        radius = req.args.get('radius', '').strip()
        data['center_location'] = location
        data['radius'] = radius
        distance = None
        if radius:
            distance, units = radius.split()
            distance = float(distance)
            if units in self.units:
                distance *= self.units[units] # to meters
            else:
                add_warning(req, "Unknown units: %s" % units)

        # filter results by PostGIS query
        ticket_ids = [ ticket['id'] for ticket in data['tickets'] ]
        if lat is not None and lon is not None and distance is not None:
            tickets_in_radius = self.query_by_radius(lat, lon, distance)
            ticket_ids = [ i for i in ticket_ids if i in tickets_in_radius ]
        region = req.args.get('region')
        if region:
            tickets_in_region = self.query_by_polygon(region)
            ticket_ids = [ i for i in ticket_ids if i in tickets_in_region ]
            column = self.env.config.get('geo', 'region-column')
            req.environ['kml'] = req.href('region.kml') + '?%s=%s' % (str(column), str(region))

        # fix up tickets
        data['tickets'] = [ ticket for ticket in data['tickets'] 
                                if ticket['id'] in ticket_ids ]


        # fix up groups
        data['groups'] = [ (group[0], [ ticket for ticket in group[1]
                                        if ticket['id'] in ticket_ids ])
                           for group in data['groups'] ]

        # fix up number of matches
        data['query'].num_items = len(data['tickets'])

        return (template, data, content_type)

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """
        # XXX monkey-patch and frame dark fancy magic:
        # http://oss.openplans.org/MobileGeoTrac/ticket/54#comment:14
        if not globals()['patched']:
            def patched_href_call(self, *args, **kw):
                frame = sys._getframe().f_back.f_back
                code = frame.f_code
                if code.co_name == 'get_href' and code.co_filename == trac.ticket.query.__file__.rstrip('c'):
                    try:
                        kw.update(self.geo_query_kw)
                    except TypeError: # XXX even more scary!
                        pass
                return original_href_call(self, *args, **kw)
            Href.__call__ = patched_href_call
            globals()['patched'] = True


        if (req.path_info == '/query' or trac.ticket.query.QueryModule == handler.__class__) and 'update' in req.args:
            match = False
            for i in 'center_location', 'radius', 'region':
                if i in req.args:
                    if not match:
                        req.href.geo_query_kw = {}
                        match = True
                    req.href.geo_query_kw[i] = req.args[i]

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
        if filename == 'query.html' and self.inject_query:
            self.geoticket() # sanity check
            chrome = Chrome(self.env)
            variables = ('center_location', 'radius')
            _data = dict([(i,data.get(i)) for i in variables])

            # georegions
            _data['geo_column_label'] = None
            _data['regions'] = None
            if self.env.is_component_enabled(GeoRegions):
                georegions = GeoRegions(self.env)
                if georegions.enabled():
                    regions = georegions.regions()
                    if regions:
                        column, regions = regions
                        _data['geo_column_label'] = column
                        _data['regions'] = regions
                        _data['region'] = req.args.get('region')

            template = chrome.load_template('geoquery.html')
            stream |= Transformer("//fieldset[@id='columns']").after(template.generate(**_data))

        return stream

    
class MapTicketsMacro(WikiMacroBase):
    """
    TicketQuery macro but with maps
    """

    def expand_macro(self, formatter, name, content):
        req = formatter.req
        query_string = ''
        argv, kwargs = parse_args(content, strict=False)

        if 'order' not in kwargs:
            kwargs['order'] = 'id'
        if 'max' not in kwargs:
            kwargs['max'] = '0' # unlimited by default

        query_string = '&'.join(['%s=%s' % item
                                 for item in kwargs.iteritems()])
        query = Query.from_string(self.env, query_string)

        tickets = query.execute(req)
        tickets = [t for t in tickets 
                   if 'TICKET_VIEW' in req.perm('ticket', t['id'])]
        ticket_ids = [ t['id'] for t in tickets ]

        # locate the tickets
        geoticket = GeoTicket(self.env)
        locations = geoticket.locate_tickets(ticket_ids, req)


        if not locations:
            return tag.div(tag.b('MapTickets: '), "No locations found for ", tag.i(content))

        data = dict(locations=Markup(simplejson.dumps(locations)),
                    query_href=query.get_href(req),
                    query_string=content)
        
        # set an id for the map
        map_id = req.environ.setdefault('MapTicketsId', 0) + 1
        req.environ['MapTicketsId'] = map_id
        data['map_id'] = 'tickets-map-%d' % map_id

        return Chrome(self.env).render_template(
            req, 'map_tickets.html', data, None, fragment=True)
