"""
 Google Webmaster Verify Plugin for Trac
 Copyright (c) March 2009  Martin Scharrer <martin@scharrer-online.de>
 This is Free Software under the BSD license.
"""

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

from trac.core import *

from  trac.web.api     import  IRequestFilter, IRequestHandler, RequestDone
from  trac.web.chrome  import  add_link,add_stylesheet,add_script #,add_meta
from  trac.config      import  ListOption


class GoogleWebmasterVerifyPlugin(Component):
    """Simply plugin to return verify webpages for Google Webmaster Service."""
    implements( IRequestHandler ) #, IRequestFilter )
    vlist = ListOption('googlewebmasterverify', 'verify', doc="Verification code(s)")
    #mvlist = ListOption('googlewebmasterverify', 'meta_verify', doc="Verification code(s) for meta tag verifcation.")

    ### methods for IRequestHandler
    def match_request(self, req):
        """Check if requested URL is '/googleXX..XX.html' where XX..XX is in
        config list."""
        try:
          path  = req.path_info
          if path.startswith("/google") and path.endswith(".html"):
            path = path[7:-5]
          else:
            return False

          if path in self.vlist:
            return True
          else:
            return False
        except:
          return False

    def process_request(self, req):
        """Send an empty HTTP 200 OK response."""
        req.send_response(200)
        req.send_header('Content-Type', 'text/plain')
        req.end_headers()
        req.write("google-site-verification: " + req.path_info[1:])
        raise RequestDone

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        self.env.log.debug("add_meta")
        if self.mvlist:
          for code in self.mvlist:
            self.env.log.debug("add_meta: " + code)
            add_meta(req,code,name="google-site-verification")

        return (template, data, content_type)

