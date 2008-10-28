""" Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
    $Id$
    $HeadURL$

    This is Free Software under the GPL v3!
""" 
from genshi.builder import Element,tag
from StringIO import StringIO
from trac.core import *
from trac.util.html import escape,Markup
from trac.wiki.api import parse_args
from trac.wiki.formatter import extract_link
from trac.wiki.macros import WikiMacroBase
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script
from urllib import urlopen,quote_plus
import md5
import re

_reWHITESPACES = re.compile(r'\s+')
_reCOMMA       = re.compile(r',\s*')
_reCOORDS      = re.compile(r'^\d+(?:\.\d*)?[:,]\d+(?:\.\d*)?$')

#_allowed_args        = ['center','zoom','size','address']
_default_map_types   = ['NORMAL','SATELLITE','HYBRID']
_supported_map_types = ['NORMAL','SATELLITE','HYBRID','PHYSICAL']
_supported_controls  = {}
for control in ( 'LargeMap', 'SmallMap', 'SmallZoom', 'Scale', \
        'MapType', 'HierarchicalMapType', 'OverviewMap' ):
    _supported_controls[control.upper()] = control

_css_units = ('em','ex','px','in','cm','mm','pt','pc')

_accuracy_to_zoom = (3, 4, 8, 10, 12, 14, 14, 15, 16, 16)

_javascript_code = """
//<![CDATA[
// TODO: move this functions to an external file:

function SetMarkerByCoords(map,lat,lng,letter) {
    map.addOverlay(new GMarker(new GLatLng(lat,lng),
        { icon: new GIcon (G_DEFAULT_ICON,
        'http://maps.google.com/mapfiles/marker'
        + letter + '.png') }
     )
    );
}

function SetMarkerByAddress(map,address,letter) {
    var geocoder = new GClientGeocoder();
    geocoder.getLatLng(
      address,
      function(point) {
        if (point) {
          SetMarkerByCoords(map, point.lat(), point.lng(), letter);
        }
      }
    )
}

$(document).ready( function () {
  if (GBrowserIsCompatible()) {
    var map = new GMap2(document.getElementById("%(id)s"),{
    //    size: new GSize(%(width)s, %(height)s),
        mapTypes: %(types_str)s
    });
    %(controls_str)s
    map.setMapType(G_%(type)s_MAP);
    if ("%(center)s") {
        map.setCenter(new GLatLng(%(center)s), %(zoom)s);
    }
    var geocoder = new GClientGeocoder();
    var address = "%(address)s";
    if (address) {
    geocoder.getLatLng(
      address,
      function(point) {
        if (!point) {
          //alert(address + " not found");
        } else {
          map.setCenter(point, %(zoom)s);
        }
      }
      )
    }
    %(markers_str)s
}} );

$(window).unload( GUnload );
//]]>
"""

class GoogleMapMacro(WikiMacroBase):
    implements(IRequestFilter)
    """ Provides a macro to insert Google Maps(TM) in Wiki pages
    """
    nid  = 0
    dbinit = 0

    def __init__(self):
        # If geocoding is done on the server side
        self.geocoding = unicode(self.env.config.get('googlemap', 'geocoding',
            "client")).lower()
        # Create DB table if it not exists.
        # but execute only once.
        if self.geocoding == 'server' and not GoogleMapMacro.dbinit:
            self.env.log.debug("Creating DB table (if not already exists).")
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS googlemapmacro (
                    id char(32) Unique,
                    lon decimal(10,6),
                    lat decimal(10,6),
                    acc decimal(2,0)
                );""")
            db.commit()
            GoogleMapMacro.dbinit = 1


    # IRequestFilter#pre_process_request
    def pre_process_request(self, req, handler):
        return handler


    # IRequestFilter#post_process_request
    def post_process_request(self, req, template, data, content_type):
        # reset macro ID counter at start of each wiki page
        GoogleMapMacro.nid = 0
        # Add Google Map JavaScript
        key = self.env.config.get('googlemap', 'api_key', None)
        if key:
            # add_script hack to support external script files:
            url = r"http://maps.google.com/maps?file=api&v=2&key=%s" % key
            scriptset = req.chrome.setdefault('scriptset', set())
            if not url in scriptset:
                script = {'href': url, 'type': 'text/javascript'}
                req.chrome.setdefault('scripts', []).append(script)
                scriptset.add(url)
        return (template, data, content_type)

    def _format_address(self, address):
        self.env.log.debug("address before = %s" % address)
        address = unicode(address).strip().replace(';',',')
        if ((address.startswith('"') and address.endswith('"')) or
            (address.startswith("'") and address.endswith("'"))):
                address = address[1:-1]
        address = _reWHITESPACES.sub(' ', address)
        address = _reCOMMA.sub(', ', address)
        self.env.log.debug("address after  = %s" % address)
        return address

    def _get_coords(self, address):
        m = md5.new()
        m.update(address)
        hash = m.hexdigest()

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        #try:
        cursor.execute("SELECT lon,lat,acc FROM googlemapmacro WHERE id='%s';" % hash)
        #except:
        #    pass
        #else:
        for row in cursor:
            if len(row) == 3:
                self.env.log.debug("Reusing coordinates from database")
                return ( str(row[0]), str(row[1]), str(row[2]) )

        response = None
        url = r'http://maps.google.com/maps/geo?output=csv&q=' + quote_plus(address)
        try:
            response = urlopen(url).read()
        except:
            raise TracError("Google Maps could not be contacted to resolve address!");
        self.env.log.debug("Google geocoding response: '%s'" % response)
        resp = response.split(',')
        if len(resp) != 4 or not resp[0] == "200":
            raise TracError("Given address '%s' couldn't be resolved by Google Maps!" % address);
        acc, lon, lat = resp[1:4]

        #try:
        cursor.execute(
            "INSERT INTO googlemapmacro (id, lon, lat, acc) VALUES ('%s', %s, %s, %s);" %
            (hash, lon, lat, acc))
        db.commit()
        self.env.log.debug("Saving coordinates to database")
        #except:
        #    pass

        return (lon, lat, acc)


    def expand_macro(self, formatter, name, content):
        largs, kwargs = parse_args(content)
        if len(largs) > 0:
            arg = unicode(largs[0]).strip(' "\'')
            if _reCOORDS.match(arg):
                if not 'center' in kwargs:
                    kwargs['center'] = arg
            else:
                if not 'address' in kwargs:
                    kwargs['address'] = arg

        # Check if Google API key is set (if not the Google Map script file
        # wasn't inserted by `post_process_request` and the map wont load)
        if not self.env.config.get('googlemap', 'api_key', None):
            raise TracError("No Google Maps API key given! Tell your web admin to get one at http://code.google.com/apis/maps/signup.html .\n")

        # Use default values if needed
        zoom = None
        size = None
        try:
            if 'zoom' in kwargs:
                zoom = unicode( int( kwargs['zoom'] ) )
            else:
                zoom = unicode( int( self.env.config.get('googlemap', 'default_zoom', "6") ) )
        except:
            raise TracError("Invalid value for zoom given! Please provide an integer from 0 to 19.")

        if 'size' in kwargs:
            size = unicode( kwargs['size'] )
        else:
            size = unicode( self.env.config.get('googlemap', 'default_size', "300x300") )


        # Get height and width
        width  = None
        height = None
        try:
            if size.find(':') != -1:
                (width,height) = size.lower().split(':')
                # Check for correct units:
                if    not width[-2:]  in _css_units \
                   or not height[-2:] in _css_units:
                       raise TracError("Wrong unit(s)!")
                # The rest must be a number:
                float( width[:-2]  )
                float( height[:-2] )
            else:
                (width,height) = size.lower().split('x')
                width  = str( int( width  ) ) + "px"
                height = str( int( height ) ) + "px"
        except:
            raise TracError("Invalid value for size given! Please provide "
                            "{width}x{height} in pixels (without unit) or "
                            "{width}{unit}:{height}{unit} in CSS units (%s)." \
                                    % ', '.join(_css_units) )


        # Correct separator for 'center' argument because comma isn't allowed in
        # macro arguments
        center = ""
        if 'center' in kwargs:
            center = unicode(kwargs['center']).replace(':',',').strip(' "\'')
            if not _reCOORDS.match(center):
                raise TracError("Invalid center coordinates given!")

        # Format address
        address = ""
        if 'address' in kwargs:
            address = self._format_address(kwargs['address'])
            if self.geocoding == 'server':
                coord = self._get_coords(address)
                center = ",".join(coord[0:2])
                address = ""
                if not 'zoom' in kwargs:
                    zoom = _accuracy_to_zoom[ int( coord[2] ) ]

        # Internal formatting functions:
        def gtyp (stype):
            return "G_%s_MAP" % str(stype)
        def gcontrol (control):
            return "map.addControl(new G%sControl());\n" % str(control)
        def gmarker (lat,lng,letter):
            letter = str(letter).upper()
            if len(letter) == 0 or letter[0] == '.':
                letter = ''
            else:
                letter = letter[0]
            return "SetMarkerByCoords(map,%s,%s,'%s');\n" % (str(lat),str(lng),letter)
        def gmarkeraddr (address,letter):
            letter = str(letter).upper()
            if len(letter) == 0 or letter[0] == '.':
                letter = ''
            else:
                letter = letter[0]
            return "SetMarkerByAddress(map,'%s','%s');\n" % (str(address),letter)

        # Set initial map type
        type = 'NORMAL'
        types = []
        types_str = None
        if 'types' in kwargs:
            types = unicode(kwargs['types']).upper().split(':')
            types_str = ','.join(map(gtyp,types))
            type = types[0]

        if 'type' in kwargs:
            type = unicode(kwargs['type']).upper()
            if 'types' in kwargs and not type in types:
                types_str += ',' + type
                types.insert(0, type)
            elif not type in _supported_map_types:
                type = 'NORMAL'
            # if types aren't set and a type is set which is supported 
            # but not a default type:
            if not 'types' in kwargs and type in _supported_map_types and not type in _default_map_types:
                   # enable type (and all default types):
                   types = _default_map_types + [type]
                   types_str = ','.join(map(gtyp,types))

        if types_str:
            types_str = '[' + types_str + ']'
        else:
            types_str = 'G_DEFAULT_MAP_TYPES'

        # Produce controls
        control_str = ""
        controls = ['LargeMap','MapType']
        if 'controls' in kwargs:
            controls = []
            for control in unicode(kwargs['controls']).upper().split(':'):
                if control in _supported_controls:
                    controls.append( _supported_controls[control] )
        controls_str = ''.join(map(gcontrol,controls))

        # Produce markers
        markers_str = ""
        if 'markers' in kwargs:
            markers = []
            for marker in unicode(kwargs['markers']).split('|'):
                if marker.find(';') != -1:
                    location, letter = marker.rsplit(';',2)
                else:
                    location = marker
                    letter   = ''
                location = self._format_address(location)
                if _reCOORDS.match(location):
                    coord = location.split(':')
                    markers.append( gmarker( coord[0], coord[1], letter ) )
                else:
                    if self.geocoding == 'server':
                        coord = []
                        if location == 'center':
                            if address:
                                coord = self._get_coords(address)
                            else:
                                coord = center.split(',')
                        else:
                            coord = self._get_coords(location)
                        markers.append( gmarker( coord[0], coord[1], letter ) )
                    else:
                        if location == 'center':
                            if address:
                                markers.append( gmarkeraddr( address, letter ) )
                            else:
                                coord = center.split(',')
                                markers.append( gmarker( coord[0], coord[1], letter ) )
                        else:
                            markers.append( gmarkeraddr( location, letter ) )
            markers_str = ''.join( markers )


        # Produce unique id for div tag
        GoogleMapMacro.nid += 1
        id = "tracgooglemap-%i" % GoogleMapMacro.nid

        # put everything in a tidy div
        html = tag.div(
                [
                    # Initialization script for this map
                    tag.script ( _javascript_code % { 'id':id,
                        'center':center,
                        'zoom':zoom, 'address':address,
                        'type':type, 'width':width, 'height':height,
                        'types_str':types_str, 'controls_str':controls_str,
                        'markers_str':markers_str
                        },
                        type = "text/javascript"),
                    # Canvas for this map
                    tag.div (
                        "Google Map is loading ... (JavaScript enabled?)",
                        id=id,
                        style= "background-color: rgb(229, 227, 223);" +
                            "width: %s; height: %s;" % (width,height),
                        )
                    ],
                class_ = "tracgooglemaps",
                );

        return html;

