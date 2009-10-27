# -*- coding: utf-8 -*-
""" Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
    $Id$
    $HeadURL$

    This is Free Software under the GPL v3!
""" 

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int(r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

from os import access,R_OK
import os.path
from trac.core import *
from trac.web.api import IRequestHandler,IRequestFilter,RequestDone
from trac.web.chrome import add_link

class ShortcutIconRequestPlugin(Component):
    """Implements the /favicon.ico handler."""
    implements(IRequestHandler,IRequestFilter)

    path    = r'/favicon.ico'
    section = 'shortcuticon'

    exttypes = {
              '.ico' : 'image/x-icon',
              '.png' : 'image/png',
              '.jpg' : 'image/jpg',
              '.gif' : 'image/gif',
            }

    def __init__(self):
        config       = self.env.config
        section      = self.section

        iconpath = config.get(section, 'iconpath')
        mimetype = config.get(section, 'mimetype')

        if not mimetype:
            try:
                idx = iconpath.rindex('.', -4)
                mimetype = self.exttypes[ iconpath[idx:] ]
            except:
                mimetype = 'image/x-icon'

        ishandler = config.getbool(section, 'handler',    True)
        isfilter  = config.getbool(section, 'linkheader', ishandler)

        self.iconpath  = iconpath
        self.mimetype  = mimetype
        self.ishandler = ishandler
        self.isfilter  = isfilter


    # IRequestHandler methods
    def match_request(self, req):
        if not self.ishandler:
            return False
        return req.path_info == self.path \
            or req.path_info == req.base_path + self.path


    def process_request(self, req):
        iconpath = self.iconpath
        iconok = False
        if iconpath:
            if os.path.isfile(iconpath) and os.access(iconpath,R_OK):
                iconok = True
            else:
                self.env.log.warning("Icon '%s' isn't a readable file!" % iconpath)
        else:
            self.env.log.warning("No icon file configured!")

        if iconok:
            req.send_file( self.iconpath, self.mimetype )
        else:
            req.send_response(404)
            req.end_headers()
#           req.send('No shortcut icon in use.', content_type='text/plain', status=404)
        raise RequestDone


    def pre_process_request(self, req, handler):
        return handler


    def post_process_request(self, req, template, data, content_type):
        if self.isfilter:
            path = req.base_path + self.path
            add_link(req, 'shortcut icon', path, None, self.mimetype)
            add_link(req, 'icon', path, None, self.mimetype)

        return (template, data, content_type)

