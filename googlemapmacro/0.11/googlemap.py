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
#import hashlib

_allowed_args        = ['center','zoom','size','address']
_default_map_types   = ['NORMAL','SATELLITE','HYBRID']
_supported_map_types = ['NORMAL','SATELLITE','HYBRID','PHYSICAL']

_javascript_code = """
//<![CDATA[
$(document).ready( function () {
  if (GBrowserIsCompatible()) {
    var map = new GMap2(document.getElementById("%(id)s"),{
     //   size: { width:%(width)s, height:%(height)s },
        mapTypes: %(types_str)s
    });
    map.addControl(new GLargeMapControl());
    map.addControl(new GMapTypeControl());
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
        if 'address' in kwargs:
            address = unicode(kwargs['address']).strip()
            if (((address[0] == '"') and (address[-1] == '"')) or
                ((address[0] == "'") and (address[-1] == "'"))):
                    address = address[1:-1]
            if not 'center' in kwargs:
                kwargs['center'] = ""

        # Correct separator for 'center' argument because comma isn't allowed in
        # macro arguments
        kwargs['center'] = unicode(kwargs['center']).replace(':',',')


        # Set initial map type
        type = 'NORMAL'
        types = ()
        types_str = None
        def gtyp (stype):
            return "G_%s_MAP" % stype
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
                        'types_str':types_str},
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

