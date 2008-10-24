""" Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
    v0.1 - Oct 2008
    This is Free Software under the GPL v3!

    $Id$
"""
from trac.core import *
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase
from StringIO import StringIO
from trac.util.html import escape,Markup

_allowed_args = ['center','zoom','size','format','maptype',
        'markers','path','span','frame','hl','key']
_google_src = r"http://maps.google.com/staticmap?"

_format = """
<img class="googlestaticmap" 
    height="%(height)s"
    width="%(width)s" 
    alt="%(alt)s"
    title="%(title)s"
    src="%(src)s"
/>
"""

_test = 1

class GoogleStaticMapMacro(WikiMacroBase):
    """ Provides a static Google Map as HTML image
    """

    def expand_macro(self, formatter, name, content):
        args, kwargs = parse_args(content)

        # HTML arguments used in Google Maps URL
        hargs = {
            'center' : "50.805935,10.349121",
            'zoom'   : "6",
            'key'    : self.env.config.get('googlestaticmap', 'api_key', None),
            'size'   : self.env.config.get('googlestaticmap', 'default_size', "300x300"),
            'hl'     : self.env.config.get('googlestaticmap', 'default_language', ""),
            }

        # Delete default zoom if user provides 'span' argument:
        if 'span' in kwargs:
            del hargs['zoom']

        # Copy given macro arguments to the HTML arguments
        for k,v in kwargs.iteritems():
            if k in _allowed_args:
                hargs[k] = v

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

        # Build URL
        src = escape( _google_src + ('&'.join([ "%s=%s" % (k,v) for k,v in hargs.iteritems() ])) )

        if not 'key' in hargs:
            raise TracError("No Google Maps API key given!\n")

        title = alt = "Google Static Map at %s" % hargs['center']
        # TODO: provide sane alternative text and image title

        if 'title' in kwargs:
            title = kwargs['title']

        out = StringIO()
        # Create HTML
        out.write( _format % { 'src':src, 'alt':alt, 'height':height,
            'width':width, 'title':title } );
        return Markup(out.getvalue())


