""" Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
    v0.1 - Oct 2008
    This is Free Software under the GPL v3!

    $Id$
"""

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

from  trac.core         import  *
from  trac.wiki.api     import  IWikiMacroProvider, parse_args
from  trac.web.href     import  Href
from  trac.config       import  Option
from  genshi.builder    import  tag

class GoogleStaticMapMacro(Component):
    """ Provides a static Google Map as HTML image.

Website: http://trac-hacks.org/wiki/GoogleStaticMapMacro

`$Id$`

== Description ==

This macro uses the
[http://code.google.com/apis/maps/documentation/staticmaps/ Google Map API] to
include '''static''' images of maps.
'''Static''' means that is is only a simple image without any user interaction 
not the usual feature-rich dynamic map on http://maps.google.com/. The positive 
side is that no javascript is needed to display the map image.

For a dynamic Google map use
[http://trac-hacks.org/wiki/GoogleMapMacro GoogleMapMacro].

The maximum size supported by Google is 640x640 pixels. If a bigger width or 
height is requested it will be reduced to 640px.

'''Important:''' A different Google Map API key is needed for every web domain 
which can be
[http://code.google.com/apis/maps/signup.html get for free from Google].

== Usage & Examples ==
=== Parameters ===
See http://code.google.com/apis/maps/documentation/staticmaps/#URL_Parameters 
for all supported arguments.
In addition the image title can be set using a `title` argument.

The map location must be given in geographic coordinates, not as address.  
Please note that the format `center=X:Y` must be used, not `center=X,Y` as 
described in the above web site, due to the way trac parses the macro.

For example:
{{{
[[GoogleStaticMap(center=50.805935:10.349121,zoom=5,size=400x400)]]
}}}

will result in the following map image:

[[Image(http://maps.google.com/staticmap?center=50.805935%2C10.349121&zoom=5&size=400x400&key=ABQIAAAAMwTA9mkyZbDS6QMcxvwm2BQk7JAK84r7ycdvlw9atwcq_yt-SxQd58w7cbhU8Fvb5JRRi4sH8vpPEQ,nolink)]]


=== Markers ===
You can add markers to the static map using the '`markers`' argument. The format 
is '`markers={latitude}:{longitude}:{size}{color}{alphanumeric-character}`', 
e.g.: `markers=50.805935:10.349121:bluea`, creates a blue marker labeled with 
'A' at 50.805935,10.349121.
Multiple marker declarations are separated using the '`|`' letter.

So,
{{{
[[GoogleStaticMap(center=50.805935:10.349121,zoom=5,size=400x400,markers=50.805935:10.349121:bluea|50.000000:10.000000:greenb|49.046195:12.117577:yellowc)]]
}}}
will result in the following map image:

[[Image(http://maps.google.com/staticmap?center=50.805935%2C10.349121&zoom=5&size=400x400&markers=50.805935%2c10.349121%2cbluea|50.000000%2c10.000000%2cgreenb|49.046195%2c12.117577%2cyellowc&key=ABQIAAAAMwTA9mkyZbDS6QMcxvwm2BQk7JAK84r7ycdvlw9atwcq_yt-SxQd58w7cbhU8Fvb5JRRi4sH8vpPEQ,nolink)]]

    """
    implements ( IWikiMacroProvider )

    key  = Option('googlestaticmap', 'api_key', None, 'Google Maps API key')
    size = Option('googlestaticmap', 'default_size', "300x300", 'Default size for map')
    hl   = Option('googlestaticmap', 'default_language', 'Default language for map')

    allowed_args = ['center','zoom','size','format','maptype',
            'markers','path','span','frame','hl','key']

    google_url = Href("http://maps.google.com/staticmap")

    def get_macros(self):
        yield 'GoogleStaticMap'

    def get_macro_description(self, name):
        return self.__doc__

    def expand_macro(self, formatter, name, content):
        args, kwargs = parse_args(content)

        # HTML arguments used in Google Maps URL
        hargs = {
              'center' : "50.805935,10.349121",
              'zoom'   : "6",
              'key'    : self.key,
              'size'   : self.size,
              'hl'     : self.hl,
            }

        # Delete default zoom if user provides 'span' argument:
        if 'span' in kwargs:
            del hargs['zoom']

        # Copy given macro arguments to the HTML arguments
        for k,v in kwargs.iteritems():
            if k in self.allowed_args:
                hargs[k] = v

        # Check if API key exists
        if not 'key' in hargs:
            raise TracError("No Google Maps API key given!\n")

        # Get height and width
        (width,height) = hargs['size'].split('x')
        if int(height) < 1:
            height = "1"
        elif int(height) > 640:
            height = "640"
        if int(width) < 1:
            width = "1"
        elif int(width) > 640:
            width = "640"
        hargs['size'] = "%sx%s" % (width,height)

        # Correct separator for 'center' argument because comma isn't allowed in
        # macro arguments
        hargs['center'] = hargs['center'].replace(':',',')

        if 'markers' in hargs:
            hargs['markers'] = hargs['markers'].replace(':',',')

        # Build URL
        src = self.google_url(**hargs)

        title = alt = "Google Static Map at %s" % hargs['center']
        # TODO: provide sane alternative text and image title

        if 'title' in kwargs:
            title = kwargs['title']

        return tag.img(
                    class_ = "googlestaticmap",
                    src    = src,
                    title  = title,
                    alt    = alt,
                    height = height,
                    width  = width,
               )

