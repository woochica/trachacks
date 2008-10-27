""" Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
    v0.1 - Oct 2008
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
from string import upper,strip
#import hashlib

_allowed_args = ('center','zoom','size','address')
_supported_map_types = ('NORMAL','SATELLITE','HYBRID','PHYSICAL')

_javascript_code = """
//<![CDATA[
$(document).ready( function () {
  if (GBrowserIsCompatible()) {
    var map = new GMap2(document.getElementById("%(id)s"));
    map.addControl(new GLargeMapControl());
    map.addControl(new GMapTypeControl());
    map.addMapType(G_%(type)s_MAP);
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
        width = int(width)
        height = int(height)
        if height < 1:
            height = "1px"
        elif height > 640:
            height = "640px"
        else:
            height = str(height) + "px"
        if width < 1:
            width = "1px"
        elif width > 640:
            width = "640px"
        else:
            width = str(width) + "px"

        # Format address
        address = ""
        if 'address' in kwargs:
            address = strip(kwargs['address'])
            if (((address[0] == '"') and (address[-1] == '"')) or
                ((address[0] == "'") and (address[-1] == "'"))):
                    address = address[1:-1]
            if not 'center' in kwargs:
                kwargs['center'] = ""

        # Correct separator for 'center' argument because comma isn't allowed in
        # macro arguments
        kwargs['center'] = kwargs['center'].replace(':',',')

        # Set initial map type
        type = 'NORMAL'
        if 'type' in kwargs:
            type = upper(kwargs['type'])
            if not type in _supported_map_types:
                type = 'NORMAL'

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
                        'type':type },
                        type = "text/javascript"),
                    # Canvas for this map
                    tag.div (
                        "",
                        id=id,
                        style="width: %s; height: %s" % (width,height),
                        )
                    ],
                class_ = "tracgooglemaps",
                );

        return html;

