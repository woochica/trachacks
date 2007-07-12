# FlashView plugin

from struct import unpack
from zlib import decompressobj
from cgi import escape as escapeHTML
import os
from trac.core import *
from trac.wiki.api import IWikiMacroProvider

def swfsize(f):
    magic, version, datasz = unpack("<3s1B1L", f.read(8))
    if ( magic != 'FWS' and magic != 'CWS' ) or datasz < 9:
        raise "Invalid format"
    datasz -= 8
    if magic == 'FWS':
        data = f.read(min(datasz, 16))
    else:
        d = decompressobj()
        data = ''
        while len( data ) < min(datasz, 16):
            data += d.decompress(f.read(64))
    data = unpack('%dB' % len(data), data)
    nbits = data[0] >> 3
    coord = {}
    q = 0
    r = 5
    for p in ('sx', 'ex', 'sy', 'ey'):
        c = nbits
        v = 0
        while c > 8:
            v <<= 8
            v |= (data[q] << r) & 0xff
            c -= 8
            q += 1
            v |= data[q] >> (8 - r)
        m = min(c, 8)
        v <<= m
        r = m - (8 - r)
        if r > 0:
            v |= (data[q] << r) & 0xff
            q += 1
            v |= data[q] >> (8 - r)
        else:
            v |= (data[q] >> -r) & ((1 << m) - 1)
            r = 8 + r
        coord[p] = v
    return (float(coord['ex'] - coord['sx']) / 20,
           float(coord['ey'] - coord['sy']) / 20)

class FlashViewMacro(Component):
    """ FlashView Macro """
    
    implements(IWikiMacroProvider)
    
    def get_macros(self):
        yield "FlashView"

    def get_macro_description(self, name):
        """Return the subclass's docstring."""
        return inspect.getdoc(self.__class__)

    def render_macro(self, req, name, content):
        # args will be null if the macro is called without parenthesis.
        if not content:
            return ''
        args = content.split(',')
        filespec = args[0]
        
        # parse filespec argument to get module and id if contained.
        parts = filespec.split(':')
        url = None
        if len(parts) == 3:                 # module:id:attachment
            if parts[0] in ['wiki', 'ticket']:
                module, id, file = parts
            else:
                raise Exception("%s module can't have attachments" % parts[0])
        elif len(parts) == 2:
            from trac.versioncontrol.web_ui import BrowserModule
            try:
                browser_links = [link for link,_ in 
                                 BrowserModule(self.env).get_link_resolvers()]
            except Exception:
                browser_links = []
            if parts[0] in browser_links:   # source:path
                module, file = parts
                rev = None
                if '@' in file:
                    file, rev = file.split('@')
                url = req.href.browser(file, rev=rev)
                raw_url = req.href.browser(file, rev=rev, format='raw')
                desc = filespec
            else: # #ticket:attachment or WikiPage:attachment
                # FIXME: do something generic about shorthand forms...
                id, file = parts
                if id and id[0] == '#':
                    module = 'ticket'
                    id = id[1:]
                elif id == 'htdocs':
                    raw_url = url = req.href.chrome('site', file)
                    desc = os.path.basename(file)
                elif id in ('http', 'https', 'ftp'): # external URLs
                    raw_url = url = desc = id+':'+file
                else:
                    module = 'wiki'
        elif len(parts) == 1:               # attachment
            # determine current object
            # FIXME: should be retrieved from the formatter...
            # ...and the formatter should be provided to the macro
            file = filespec
            module, id = 'wiki', 'WikiStart'
            path_info = req.path_info.split('/',2)
            if len(path_info) > 1:
                module = path_info[1]
            if len(path_info) > 2:
                id = path_info[2]
            if module not in ['wiki', 'ticket']:
                raise Exception('Cannot reference local attachment from here')
        else:
            raise Exception('No filespec given')
        if not url: # this is an attachment
            from trac.attachment import Attachment
            attachment = Attachment(self.env, module, id, file)
            url = attachment.href(req)
            raw_url = attachment.href(req, format='raw')
            desc = attachment.description
            width, height = swfsize(attachment.open())
            if len(args) == 3:
                if args[1][0] == '*':
                    width = int(width * float(args[1][1:]))
                else:
                    width = args[1]
                if args[2][0] == '*':
                    height = int(height * float(args[2][1:]))
                else:
                    height = args[2]
            elif len(args) != 1:
                raise Exception('Too few arguments. (filespec, width, height)')
        else:
            if len(args) < 3:
                raise Exception('Too few arguments. (filespec, width, height)')
            else:
                width = args[1]
                height = args[2]

        vars = {
            'width': width,
            'height': height,
            'raw_url': raw_url
            }

        return """
<object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000"
        codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab"
        width="%(width)s" height="%(height)s">
  <param name="movie" value="%(raw_url)s">
  <param name="quality" value="low">
  <param name="play" value="true">
  <embed src="%(raw_url)s" quality="low" width="%(width)s" height="%(height)s"
         type="application/x-shockwave-flash"
         pluginspage="http://www.macromedia.com/go/getflashplayer">
  </embed>
</object>
        """ % dict(map(lambda i: (i[0], escapeHTML(str(i[1]))), vars.items()))
