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
#import hashlib

_allowed_args = ['center','zoom','size','address']

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
            #add_script(req, r"http://maps.google.com/maps?file=api&v=2&key=%s" % key )

            # add_script hack to support external script files:
            url = r"http://maps.google.com/maps?file=api&v=2&key=%s" % key
            scriptset = req.chrome.setdefault('scriptset', set())
            if not url in scriptset:
                script = {'href': url, 'type': 'text/javascript'}
                req.chrome.setdefault('scripts', []).append(script)
                scriptset.add(url)
        return (template, data, content_type)


    def expand_macro(self, formatter, name, content):
        args, kwargs = parse_args(content)
        if len(args) > 0 and not 'address' in kwargs:
            kwargs['address'] = args[0]

        # HTML arguments used in Google Maps URL
        hargs = {
            'center' : "50.805935,10.349121",
            'zoom'   : "6",
            'size'   : self.env.config.get('googlemap', 'default_size', "300x300"),
           # 'hl'     : self.env.config.get('googlemap', 'default_language', ""),
            }

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
        (width,height) = hargs['size'].split('x')
        width = int(width)
        height = int(height)
        if height < 1:
            height = 1
        elif height > 640:
            height = 640
        else:
            height = str(height) + "px"
        if width < 1:
            width = 1
        elif width > 640:
            width = 640
        else:
            width = str(width) + "px"

        address = ""
        if 'address' in hargs:
            address = hargs['address']
            if (((address[0] == '"') and (address[-1] == '"')) or
                ((address[0] == "'") and (address[-1] == "'"))):
                    address = address[1:-1]
            if not 'center' in kwargs:
                hargs['center'] = ""

        # Correct separator for 'center' argument because comma isn't allowed in
        # macro arguments
        hargs['center'] = hargs['center'].replace(':',',')

        # Build URL
        #src = _google_src + ('&'.join([ "%s=%s" % (escape(k),escape(v)) for k,v in hargs.iteritems() ]))

        #title = alt = "Google Static Map at %s" % hargs['center']
        # TODO: provide sane alternative text and image title

        #if 'title' in kwargs:
        #    title = kwargs['title']
        type = 'NORMAL'
        if 'type' in kwargs:
            type = kwargs['type'].upper()
            if not type in ('NORMAL','SATELLITE','HYBRID','PHYSICAL'):
                type = 'NORMAL'

        # Produce unique id for div tag
        GoogleMapMacro.nid += 1
        #idhash = hashlib.md5()
        #idhash.update( content )
        #id = "tracgooglemap-%i-%s" % (GoogleMapMacro.nid, idhash.hexdigest())
        id = "tracgooglemap-%i" % GoogleMapMacro.nid


        html = tag.div(
                [
        #        tag.script (
        #            "",
        #            src  = ( r"http://maps.google.com/maps?file=api&v=2&key=%s" % hargs['key'] ),
        #            type = "text/javascript",
        #        ),
                tag.script (
                    """
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
                    """ % { 'id':id, 'center':hargs['center'],
                        'zoom':hargs['zoom'], 'address':address,
                        'type':type },
                    type = "text/javascript"),
                tag.div (
                    "",
                    id=id,
                    style="width: %s; height: %s" % (width,height),
                )
                ],
                class_ = "tracgooglemaps",
                );

        return html;

