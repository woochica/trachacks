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

from pkg_resources import resource_filename

import sys, os
import time

__all__ = ['ImageSvg']

class ImageSvg(Component):
    implements(
               IRequestHandler, 
               )

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith("/svg")


    def process_request(self, req):
        if req.path_info.startswith("/svg"):
            pathSegs = req.path_info.split("/")
            image_path = "/".join(pathSegs[2:])
            f = os.path.join(self.env.path, image_path)
            try:
                message = open(f).read()
            except:
                raise HTTPException(404)

            req.send_response(200)
            req.send_header('Cache-control', 'no-cache')
            req.send_header('Expires', 'Fri, 01 Jan 1999 00:00:00 GMT')
            req.send_header('Content-Type', 'image/svg+xml')
            req.send_header('Content-Length', len(message))
            req.end_headers()

            if req.method != 'HEAD':
                req.write(message)
            raise RequestDone
