# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         web_ui.py
# Purpose:      The image svg file handler module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

from trac.core import *
from trac.web.chrome import *
from trac.util.html import html

from trac.web import IRequestHandler
from trac.web.api import RequestDone, HTTPException
from trac.attachment import Attachment
from trac.wiki.api import IWikiMacroProvider

from pkg_resources import resource_filename

import sys, os
import time
import inspect

__all__ = ['ImageSvg']

class ImageSvg(Component):
    revision = "$Rev$"
    url = "$URL$"

    implements(
               IWikiMacroProvider, 
               IRequestHandler, 
               )

    # IWikiMacroProvider methods
    def get_macros(self):
        yield "ImageSvg"
        
    def get_macro_description(self, name):
        return inspect.getdoc(self.__class__)

    def expand_macro(self, formatter, name, content):
        # args will be null if the macro is called without parenthesis.
        if not content:
            return ''
        # parse arguments
        # we expect the 1st argument to be a filename (filespec)
        args = content.split(',')
        if len(args) == 0:
           raise Exception("No argument.")
        if len(args) == 3:
           targetSize = "width='%(w)s'height='%(h)s'" % {'w': args[1].strip(), 'h': args[2].strip()}
        else:
           targetSize = None
        filespec = args[0]
        # parse filespec argument to get module and id if contained.
        parts = filespec.split(':')
        if len(parts) == 3:                 # module:id:attachment
            if parts[0] in ['wiki', 'ticket']:
                module, id, file = parts
            else:
                raise Exception("%s module can't have attachments" % parts[0])
        elif len(parts) == 2:               # #ticket:attachment or WikiPage:attachment
            # FIXME: do something generic about shorthand forms...
            id, file = parts
            if id and id[0] == '#':
                module = 'ticket'
                id = id[1:]
            else:
                module = 'wiki'
        elif len(parts) == 1:               # attachment
            file = filespec
            parts = formatter.req.path_info.split("/")
            if len(parts) >= 3:
                module = parts[1]
                id =''
                for p in parts[2:]:
                    if len(id) > 0:
                        id = id + "/"
                    id = id + p
            elif len(parts) == 0:
                module = "wiki"
                id = "WikiStart"
            else:
                # limit of use
                raise Exception("Cannot use this macro in this module (len(parts)=%d, file=%s, path_info=%s, parts=%s)" % (len(parts), file, formatter.req.path_info, parts))

        else:
            raise Exception( 'No filespec given' )

        try:
            attachment = Attachment(self.env, module, id, file)
            org_path = attachment.path
            try:
                if targetSize is None:
                    f = open(org_path, 'r')
                    svg = f.readlines()
                    f.close()
                    svg = "".join(svg).replace('\n', '')
                else:
                    svg = targetSize
                w = re.search('''width=["']([0-9]+\.?[0-9]?)(.*?)["']''', svg)
                h = re.search('''height=["']([0-9]+\.?[0-9]?)(.*?)["']''', svg)
                (w_val, w_unit) = w.group(1,2)
                (h_val, h_unit) = h.group(1,2)
                w_unit = w_unit.strip()
                h_unit = h_unit.strip()

                unitMapping = {
                    "cm": 72 / 2.54,
                    "mm": 72 / 25.4,
                    "in": 72 / 1,
                    "pc": 72 / 6,
                    "": 1,
                }

                import math
                if w_unit in unitMapping.keys():
                    w_val = int(math.ceil(float(w_val) * unitMapping[w_unit]))
                    h_val = int(math.ceil(float(h_val) * unitMapping[w_unit]))
                    w_unit = "pt"
                    h_unit = "pt"


                dimensions = 'width="%(w_val)s%(w_unit)s" height="%(h_val)s%(h_unit)s"' % locals()
            except:
                dimensions = 'width="100%" height="100%"'

            data = {
                "base_url": self.env.base_url,
                "module": module,
                "id": id,
                "file": file,
                "dimensions": dimensions,
                }
            s = '''
            <div>
            <embed  type="image/svg+xml" 
                style="margin: 0pt; padding: 0pt;"
                src="%(base_url)s/svg/attachments/%(module)s/%(id)s/%(file)s"  
                %(dimensions)s
                pluginspage="http://www.adobe.com/svg/viewer/install/"> 
            </embed>
            </div>
            ''' % data
            return s
        except:
            return '%s not found' % (filespec)

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith("/svg")


    def process_request(self, req):
        if req.path_info.startswith("/svg"):
            # ["", "svg", "attachments", "wiki" or "ticket", filename.ext...]
            parts = req.path_info.split("/")
            attachment = Attachment(self.env, parts[3], "/".join(parts[4:-1]))
            attachment.filename = parts[-1]
            try:
                message = open(attachment.path).read()
            except:
                raise HTTPException(404)

            req.send_response(200)
            req.send_header('Cache-control', 'no-cache')
            req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
            req.send_header('Content-Type', 'image/svg+xml')
            req.send_header('Content-Length', len(isinstance(message, unicode) and message.encode("utf-8") or message))
            req.end_headers()

            if req.method != 'HEAD':
                req.write(message)
            raise RequestDone
