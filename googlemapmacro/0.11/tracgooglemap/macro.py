""" Copyright (c) 2008-2010 Martin Scharrer <martin@scharrer-online.de>
    $Id$
    $HeadURL$

    This is Free Software under the GPL v3!
"""

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]

from genshi.builder import Element,tag
from StringIO import StringIO
from trac.core import *
from trac.util import md5
from trac.util.html import escape,Markup
from tracadvparseargs import parse_args
from trac.wiki.formatter import extract_link
from trac.wiki.macros import WikiMacroBase
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_link, add_script
from trac.env import IEnvironmentSetupParticipant
from genshi.builder import Element
from urllib import urlopen,quote_plus
from trac.config import Option, IntOption
import re

COUNT = '_googlemapmacro_count'

_reWHITESPACES = re.compile(r'\s+')
_reCOMMA       = re.compile(r',\s*')
_reCOORDS      = re.compile(r'^[+-]?\d+(?:\.\d*)?[:,][+-]?\d+(?:\.\d*)?$')
_reDBLQUOTE    = re.compile(r'(?<!\\)"')

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

TracGoogleMap( function (mapdiv,index) {
    var map = new GMap2(mapdiv, {
    //    size: new GSize(%(width)s, %(height)s),
        mapTypes: %(types_str)s
    });
    %(controls_str)s
    map.setMapType(G_%(type)s_MAP);
    if ("%(center)s") {
        map.setCenter(new GLatLng(%(center)s), %(zoom)s);
    }
    var geocoder = new GClientGeocoder();
    var address  = "%(address)s";
    if (address) {
        geocoder.getLatLng(
            address,
            function(point) {
                if (point) {
                    map.setCenter(point, %(zoom)s);
                }
            }
        )
    }
    %(markers_str)s
    if ("%(directions)s") {
        dirdiv = document.getElementById("tracgooglemap-directions-" + index);
        gdir = new GDirections(map, dirdiv);
        gdir.load("%(directions)s");
    }
}, "%(id)s" );

//]]>
"""

class GoogleMapMacro (WikiMacroBase):
    """ Provides a macro to insert Google Maps(TM) in Wiki pages.

== Description ==

Website: http://trac-hacks.org/wiki/GoogleMapMacro

`$Id$`

This macro lets the user insert a full dynamic
[http://maps.google.com/ Google Map]. Because a lot of javascript is used (by 
Google) a
[http://local.google.com/support/bin/answer.py?answer=16532&amp;topic=1499 Google Map compatible browser]
is needed. Newer version of Firefox and MS Internet Explorer are compatible.

For javascript-less static maps use the similar
[http://trac-hacks.org/wiki/GoogleStaticMapMacro GoogleStaticMapMacro].

Multiple Google Maps on the same wiki page are actively supported.

== Dependencies ==
The recent version (r480) of this macro needs the AdvParseArgsPlugin in revision 
4795 or later.

== Configuration ==

A different [http://code.google.com/apis/maps/signup.html Google Map API key] is 
needed for every web domain which can be get for free from Google.
'''Please check if the Google Map API Terms of Use apply for your Trac 
project.''' They do apply IMHO for non-pay open accessible Trac projects.

== Usage ==
The macro knows the following arguments, which can be used in the normal 
`key1=value1,key2=value2,...` syntax. If a value includes one or more comma then 
it must be set in double quotes (`" "`).
If a key-less value is given it will be taken as `center` coordinates if it's in 
the proper format otherwise it's taken as an `address`. Unknown (or misspelled) 
keys or key-less values except the first are silently ignored.

 `address`:: Sets the center of the map to the given address. The value must be
             surrounded by quotes if it includes commas, e.g. `"Street, City, 
             Country"`.
             If an `address` but no `zoom` value was given an appropriate value 
             will be guessed based on the address accuracy returned by Google.
             At the moment this isn't very accurate but soon 
             [http://groups.google.com/group/Google-Maps-API/browse_thread/thread/53c4525e8d01e75d Google might improve] this.
 `center`:: Sets the center of the map to the given coordinates. The format is `{latitude}:{longitude}` or `"{latitude},{longitude}"`.
 `zoom`:: Sets zoom factor. Allowed values are between 0 (whole world) and 19 (single house). Very high zoom values might not be supported by Google Maps for all parts of the world.
 `size`:: The size either in the format `{width}x{height}` as numbers in pixel, e.g.: `300x400` means 300px wide and 400px high or
          in the format `{width}{unit}:{height}{unit}` where unit can be any CSS unit (em, ex, px, in, cm, mm, pt, pc).
 `types` (optional):: Sets the map types selectable by the user, separated by colons ('`:`'). If not given the standard types of Google Maps are used (Normal, Satellite, Hybrid). The following types are available (values are case-insensitive):
   * `normal` Normal street-map
   * `satellite` Satellite picture
   * `hybrid` Satellite picture with streets as overlay
   * `physical` Terrain map
 `type` (optional):: Sets the initial map type. See the `types` argument for the available types. If this argument is not given the first listed type under `types` is used initially.
 `controls` (optional):: Sets the used map controls. Multiple controls can be given, separated by colon ('`:`'). The value is case-insensitive. If not set the controls `MapType` and `LargeMap` are used. 
 If set but empty no controls are displayed. The following controls are available (descriptions taken from the [http://code.google.com/apis/maps/documentation/reference.html#GControlImpl Google Map API page]):
   * `LargeMap`: Control with buttons to pan in four directions, and zoom in and zoom out.
   * `SmallMap`: Control with buttons to pan in four directions, and zoom in and zoom out, and a zoom slider.
   * `SmallZoom`: Control with buttons to zoom in and zoom out.
   * `Scale`: Control that displays the map scale.
   * `MapType`: Standard map type control for selecting and switching between supported map types via buttons. 
   * `HierarchicalMapType`: Drop-down map type control for switching between supported map types.
   * `OverviewMap`: Collapsible overview mini-map in the corner of the main map for reference location and navigation (through dragging).
 `marker`:: (New) Allows the user to set labeled markers on given location of the map. 
    The format for a marker is `{latitude}:{longitude};{Letter};{TracLink};{Title}` or `"{Address}";{Letter};{TracLink};{Title}`.
    If the string 'center' is used instead of an address the center of the map is marked.
    The optional marker letter can be either A-Z or 'o', '.' or empty for a plain marker.
    An optional [TracLinks TracLink] can be given which may be opened in a new window (see `target`) when clicked on the marker.
    An optional marker title can be set which will get displayed when the mouse cursor is over the marker.
    From revision [4801] on multiple markers can be given which replaces the `markers` argument.
 `markers`:: (Old) Can be used to set multiple markers which are are separated using the '`|`' character.
    Optional values can be kept empty, e.g.: `"{Address}";;;My Address` would display the address with the title 'My Address'.
    Trailing semicolons can be skipped. Addresses, links and titles which include either '`,`', '`;`' or '`|`' must be enclosed in double quotes (`" "`).
 `target`:: If set to '`new`' or '`newwindow`' all hyperlinks of the map markers will be opened in a new window (or tab, depending on the browser settings) or in the same window otherwise.
 `from`,`to`:: Request driving directions '`from`'->'`to`'. Multiple `to` addresses are allowed. No `address` or `center` need to be given.

== Examples ==

=== Using geographic coordinates ===
Please use a colon, not a comma, as separator for the coordinates.
{{{
[[GoogleMap(center=50.0:10.0,zoom=10,size=400x400)]]
or
[[GoogleMap("50.0:10.0",zoom=10,size=400x400)]]
or
[[GoogleMap(50.0:10.0,zoom=10,size=400x400)]]
}}}
=== Using an address ===
Please use semicolons, not commas, as separators in the address.
{{{
[[GoogleMap(address="Street, City, Country",zoom=10,size=400x400)]]
or
[[GoogleMap("Street, City, Country",zoom=10,size=400x400)]]
or, if you really want to:
[[GoogleMap(Street; City; Country,zoom=10,size=400x400)]]
}}}
Please note that the address is converted into coordinates by user-side javascript every time the wiki page is loaded.
If this fails no map will be shown, only an empty gray rectangle.

=== Using both ===
If both address and center coordinates are given, then the result depends on the [#config `geocoding` setting]:
 `server`:: The address is resolved on the trac server and the coordinates are completely ignored.
 `client`:: The map is first centered at the given coordinates and then moved to the given address after (and if) it was 
            resolved by the client-side !JavaScript code.
{{{
[[GoogleMap(center=50.0:10.0,address="Street, City, Country",zoom=10,size=400x400)]]
}}}

=== Select Map Types ===
To show a map with the standard map types where the satellite map is preselected:
{{{
[[GoogleMap("Street, City, Country",zoom=10,size=400x400,type=satellite)]]
}}}

To only show a satellite map (please note the added '`s`'):
{{{
[[GoogleMap("Street, City, Country",zoom=10,size=400x400,types=satellite)]]
}}}

To show a map with hybrid and satellite map types (in this order) where the satellite map is preselected:
{{{
[[GoogleMap("Street, City, Country",zoom=10,size=400x400,types=hybrid:satellite,type=satellite)]]
}}}

To show a map with hybrid and satellite map types (in this order) where the hybrid map is preselected:
{{{
[[GoogleMap("Street, City, Country",zoom=10,size=400x400,types=hybrid:satellite)]]
or
[[GoogleMap("Street, City, Country",zoom=10,size=400x400,types=hybrid:satellite,type=hybrid)]]
}}}

=== Markers ===
To create three markers: one at the center of the map (A), one at the next street (B) and one at coordinates 10.243,23.343 (C):
{{{
[[GoogleMap("Street, City, Country",zoom=10,size=400x400,markers=center;A|"Next street, City, Country";B|10.243:23.343;C)]]
}}}
The same with hyperlinked markers:
{{{
[[GoogleMap("Street, City, Country",zoom=10,size=400x400,markers=center;A;wiki:MyWikiPage|"Next street, City, Country";B;ticket:1|10.243:23.343;C;http://www.example.com/)]]
}}}
    """
    implements(IRequestFilter,ITemplateProvider,IRequestFilter,IEnvironmentSetupParticipant)

    geocoding = Option('googlemap','geocoding','client','Which side is handling the geocoding: either "server" or "client" (default).')
    api_key   = Option('googlemap', 'api_key', '', 'Google Map API key. Available from http://code.google.com/apis/maps/signup.html .')
    default_zoom = IntOption('googlemap', 'default_zoom', '6', 'Default map zoom used if no zoom specified by the user (default: 6)')
    default_size =    Option('googlemap', 'default_size', '300x300', 'Default map size (width x height, in pixel without units) used if no size specified by the user (default: 300x300)')
    default_target =  Option('googlemap', 'default_target', '', 'Default target for hyperlinked markers. Use "_blank" to open target in new window. (Default: "")')

    def __init__(self):
        self.geocoding_server = self.geocoding.lower() == "server"

    def _create_db_table(self, db=None, commit=True):
        """ Create DB table if it not exists. """
        if self.geocoding_server:
            self.env.log.debug("Creating DB table (if not already exists).")

            db = db or self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS googlemapmacro (
                    id char(32) Unique,
                    lon decimal(10,6),
                    lat decimal(10,6),
                    acc decimal(2,0)
                );""")
            if commit:
                db.commit()
        return


    def environment_created(self):
        self._create_db_table()
        return

    def environment_needs_upgrade(self, db):
        if not self.geocoding_server:
            return False
        cursor = db.cursor()
        try:
            cursor.execute("SELECT count(*) FROM googlemapmacro;")
            cursor.fetchone()
        except:
            return True
        return False

    def upgrade_environment(self, db):
        self._create_db_table(db, False)
        return


    # ITemplateProvider#get_htdocs_dirs
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('googlemap', resource_filename(__name__, 'htdocs'))]

    # ITemplateProvider#get_templates_dirs
    def get_templates_dirs(self):
        return []


    # IRequestFilter#pre_process_request
    def pre_process_request(self, req, handler):
        return handler


    # IRequestFilter#post_process_request
    def post_process_request(self, req, template, data, content_type):
        # Add Google Map API key using a link tag:
        if self.api_key:
            add_link (req, rel='google-key', href='', title=self.api_key, classname='google-key')
            add_script (req, 'googlemap/tracgooglemap.js')
        return (template, data, content_type)

    def _strip(self, arg):
        """Strips spaces and a single pair of double quotes as long there are 
           no unescaped double quotes in the middle.  """
        arg = unicode(arg).strip()
        if len(arg) < 2:
            return arg
        if arg.startswith('"') and arg.endswith('"') \
           and not _reDBLQUOTE.match(arg[1:-1]):
            arg = arg[1:-1]
        return arg

    def _format_address(self, address):
        address = self._strip(address).replace(';',',')
        address = _reWHITESPACES.sub(' ', address)
        address = _reCOMMA.sub(', ', address)
        return address


    def _get_coords(self, address):
        m = md5()
        m.update(address)
        hash = m.hexdigest()

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT lon,lat,acc FROM googlemapmacro WHERE id='%s';" % hash)
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

        cursor.execute(
            "INSERT INTO googlemapmacro (id, lon, lat, acc) VALUES ('%s', %s, %s, %s);" %
            (hash, lon, lat, acc))
        db.commit()
        self.env.log.debug("Saving coordinates to database")

        return (lon, lat, acc)

    def expand_macro(self, formatter, name, content):
        largs, kwargs = parse_args(content, multi=['marker','to'])
        if len(largs) > 0:
            arg = unicode(largs[0])
            if _reCOORDS.match(arg):
                if not 'center' in kwargs:
                    kwargs['center'] = arg
            else:
                if not 'address' in kwargs:
                    kwargs['address'] = arg
        if 'from' in kwargs and not 'address' in kwargs and not 'center' in kwargs:
            arg = unicode(kwargs['from'])
            if _reCOORDS.match(arg):
                if not 'center' in kwargs:
                    kwargs['center'] = arg
            else:
                if not 'address' in kwargs:
                    kwargs['address'] = arg

        # Check if Google API key is set (if not the Google Map script file
        # wasn't inserted by `post_process_request` and the map wont load)
        if not self.api_key:
            raise TracError("No Google Maps API key given! Tell your web admin to get one at http://code.google.com/apis/maps/signup.html .\n")

        # Use default values if needed
        zoom = None
        size = None
        try:
            if 'zoom' in kwargs:
                zoom = unicode( int( kwargs['zoom'] ) )
            else:
                zoom = unicode( self.default_zoom )
        except:
            raise TracError("Invalid value for zoom given! Please provide an integer from 0 to 19.")

        if 'size' in kwargs:
            size = unicode( kwargs['size'] )
        else:
            size = unicode( self.default_size )

        # Set target for hyperlinked markers
        target = ""
        if not 'target' in kwargs:
            kwargs['target'] = self.default_target
        if kwargs['target'] in ('new','newwindow','_blank'):
            target = "newwindow"

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
            if self.geocoding_server:
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
        def gmarker (lat,lng,letter='',link='',title=''):
            if not title:
                title = link
            if not letter:
                letter = ''
            else:
                letter = str(letter).upper()
                if str(letter).startswith('.'):
                    letter = ''
                else:
                    letter = letter[0]
            return "SetMarkerByCoords(map,%s,%s,'%s','%s','%s', '%s');\n" \
                    % (str(lat),str(lng),letter,str(link),str(title),str(target))
        def gmarkeraddr (address,letter='',link='',title=''):
            if not title:
                title = link
            if not letter:
                letter = ''
            else:
                letter = str(letter).upper()
                if str(letter).startswith('.'):
                    letter = ''
                else:
                    letter = letter[0]
            return "SetMarkerByAddress(map,'%s','%s','%s','%s','%s',geocoder);\n" \
                    % (str(address),letter,str(link),str(title),str(target))

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
        if not 'marker' in kwargs:
            kwargs['marker'] = []
        if 'markers' in kwargs:
            kwargs['marker'].extend( parse_args( unicode(kwargs['markers']), delim='|',
                                      listonly=True) )
        if kwargs['marker']:
            markers = []
            for marker in kwargs['marker']:
                location, letter, link, title = parse_args( marker,
                        delim=';', listonly=True, minlen=4 )[:4]
                if not title:
                    title = link

                # Convert wiki to HTML link:
                link = extract_link(self.env, formatter.context, link)
                if isinstance(link, Element):
                    link = link.attrib.get('href')
                else:
                    link = ''

                location = self._format_address(location)
                if _reCOORDS.match(location):
                    coord = location.split(':')
                    markers.append( gmarker( coord[0], coord[1], letter, link, title ) )
                else:
                    if self.geocoding_server:
                        coord = []
                        if location == 'center':
                            if address:
                                coord = self._get_coords(address)
                            else:
                                coord = center.split(',')
                        else:
                            coord = self._get_coords(location)
                        markers.append( gmarker( coord[0], coord[1], letter, link, title ) )
                    else:
                        if location == 'center':
                            if address:
                                markers.append( gmarkeraddr( address, letter, link, title ) )
                            else:
                                coord = center.split(',')
                                markers.append( gmarker( coord[0], coord[1], letter, link, title ) )
                        else:
                            markers.append( gmarkeraddr( location, letter, link, title) )
            markers_str = ''.join( markers )

        # Get macro count from request object
        req = formatter.req
        count = getattr (req, COUNT, 0)
        id = 'tracgooglemap-%s' % count
        setattr (req, COUNT, count + 1)

        # Canvas for this map
        mapdiv = tag.div (
                    "Google Map is loading ... (JavaScript enabled?)",
                    id=id,
                    style = "width: %s; height: %s;" % (width,height),
                    class_ = "tracgooglemap"
                )

        if 'from' in kwargs and 'to' in kwargs:
            directions = "from: %s to: %s" % (kwargs['from'],' to: '.join(list(kwargs['to'])))
            mapnmore = tag.table(
                            tag.tr(
                                tag.td(
                                    tag.div( "", 
                                        class_ = 'tracgooglemap-directions',
                                        id     = 'tracgooglemap-directions-%s' % count
                                    ),
                                    style="vertical-align:top;",
                                ),
                                tag.td(
                                    mapdiv,
                                    style="vertical-align:top;",
                                )
                            ),
                          class_ = 'tracgooglemaps'
                       )

        else:
            directions = ""
            mapnmore = mapdiv

        # put everything in a tidy div
        html = tag.div(
                [
                    # Initialization script for this map
                    tag.script ( Markup( _javascript_code % { 'id':id,
                        'center':center,
                        'zoom':zoom, 'address':address,
                        'type':type, 'width':width, 'height':height,
                        'types_str':types_str, 'controls_str':controls_str,
                        'markers_str':markers_str, 'directions':directions,
                        } ),
                        type = "text/javascript"),
                    mapnmore
                    ],
                class_ = "tracgooglemap-parent"
                );

        return html;

