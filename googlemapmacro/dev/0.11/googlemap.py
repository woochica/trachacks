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
_reWHITEENDS   = re.compile(r'(?:^\s+|\s+$)')
_reCOMMA       = re.compile(r',\s*')
_reCOMMA       = re.compile(r',\s*')

_allowed_args        = ['center','zoom','size','address']
_default_map_types   = ['NORMAL','SATELLITE','HYBRID']
_supported_map_types = ['NORMAL','SATELLITE','HYBRID','PHYSICAL']
_supported_controls  = [ 'LargeMap', 'SmallMap', 'SmallZoom', 'Scale', \
                        'MapType', 'HierarchicalMapType', 'OverviewMap' ]

_javascript_code = """
//<![CDATA[
$(document).ready( function () {
  if (GBrowserIsCompatible()) {
    var map = new GMap2(document.getElementById("%(id)s"),{
     //   size: { width:%(width)s, height:%(height)s },
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
}} );

$(window).unload( GUnload );
//]]>
"""

class GoogleMapMacro(WikiMacroBase):
    implements(IRequestFilter)
    """ Provides a macro to insert Google Maps(TM) in Wiki pages
    """
    nid = 0


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
        address = address.replace(';',',')
        if ((address.startswith('"') and address.endswith('"')) or
            (address.startswith("'") and address.endswith("'"))):
                address = address[1:-1]
        address = _reWHITEENDS.sub('', address)
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
        cursor.execute("SELECT lon,lat FROM googlemapmacro WHERE id='%s'" % hash)
        #except:
        #    pass
        #else:
        for row in cursor:
            if len(row) == 2:
                self.env.log.debug("Reusing coordinates from database")
                return ( str(row[0]), str(row[1]) )

        response = None
        url = r'http://maps.google.com/maps/geo?output=csv&q=' + quote_plus(address)
        try:
            response = urlopen(url).read()
        except:
            return
        resp = response.split(',')
        if len(resp) != 4 or not resp[0] == "200":
            return
        lon, lat = resp[2:4]

        #try:
        cursor.execute(
            "INSERT INTO googlemapmacro VALUES ('%s', %s, %s)" %
            (hash, lon, lat))
        db.commit()
        self.env.log.debug("Saving coordinates to database")
        #except:
        #    pass

        return (lon, lat)


    def expand_macro(self, formatter, name, content):
        largs, kwargs = parse_args(content)
        if len(largs) > 0 and not 'address' in kwargs:
            kwargs['address'] = largs[0]

        # Use default values if needed
        if not 'zoom' in kwargs:
            kwargs['zoom'] = self.env.config.get('googlemap', 'default_zoom', "6"),
        if not 'size' in kwargs:
            kwargs['size'] = self.env.config.get('googlemap', 'default_size', "6"),

        # Check if Google API key is set (if not the Google Map script file
        # wasn't inserted by `post_process_request` and the map wont load)
        key = self.env.config.get('googlemap', 'api_key', None)
        if not key:
            raise TracError("No Google Maps API key given! Tell your web admin to get one at http://code.google.com/apis/maps/signup.html .\n")


        ## Delete default zoom if user provides 'span' argument:
        #if 'span' in kwargs:
        #    del hargs['zoom']

        # Copy given macro arguments to the HTML arguments
        for k,v in kwargs.iteritems():
            if k in _allowed_args:
                hargs[k] = v

        # Get height and width
        (width,height) = kwargs['size'].split('x')
        width  = int(width)
        height = int(height)
        if height < 1:
            height = "1"
        elif height > 640:
            height = "640"
        else:
            height = str(height)
        if width < 1:
            width = "1"
        elif width > 640:
            width = "640"
        else:
            width = str(width)

        # Format address
        address = ""
        if 'address' in hargs:
            address = self._format_address(hargs['address'])
            if not 'center' in kwargs:
                coord = self._get_coords(address)
                if not coord or len(coord) != 2:
                    raise TracError("Given address '%s' couldn't be resolved by Google Maps!" % address);
                hargs['center'] = ",".join(coord)
                hargs['address'] = "" # delete address when coordinates are resolved
                address = ""

        # Correct separator for 'center' argument because comma isn't allowed in
        # macro arguments
        kwargs['center'] = unicode(kwargs['center']).replace(':',',')

        # Internal formatting functions:
        def gtyp (stype):
            return "G_%s_MAP" % stype
        def gcontrol (control):
            return "map.addControl(new G%sControl());\n" % control

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
            for control in unicode(kwargs['controls']).split(':'):
                if control in _supported_controls:
                    controls.append(control)
        controls_str = ''.join(map(gcontrol,controls))


        # Produce unique id for div tag
        GoogleMapMacro.nid += 1
        id = "tracgooglemap-%i" % GoogleMapMacro.nid

        # put everything in a tidy div
        html = tag.div(
                [
                    # Initialization script for this map
                    tag.script ( _javascript_code % { 'id':id,
                        'center':kwargs['center'],
                        'zoom':kwargs['zoom'], 'address':address,
                        'type':type, 'width':width, 'height':height,
                        'types_str':types_str, 'controls_str':controls_str },
                        type = "text/javascript"),
                    # Canvas for this map
                    tag.div (
                        "",
                        id=id,
                        style="width: %spx; height: %spx" % (width,height),
                        )
                    ],
                class_ = "tracgooglemaps",
                );

        return html;

