"""
 Google Webmaster Verify Plugin for Trac
 Copyright (c) March 2009  Martin Scharrer <martin@scharrer-online.de>
 This is Free Software under the BSD license.
"""

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int(r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

from trac.core import *

from  trac.web.api     import  IRequestFilter, IRequestHandler, RequestDone

class GoogleWebmasterVerifyPlugin(Component):
    """Simply plugin to return verify webpages for Google Webmaster Service."""
    implements( IRequestHandler )

    ### methods for IRequestHandler
    def match_request(self, req):
        """Check if requested URL is '/googleXX..XX.html' where XX..XX is in
        config list."""
        try:
          vlist = self.config.getlist('googlewebmasterverify', 'verify')
          path  = req.path_info
          if path.startswith("/google") and path.endswith(".html"):
            path = path[7:-5]
          else:
            return False

          if path in vlist:
            return True
          else:
            return False
        except:
          return False

    def process_request(self, req):
        """Send an empty HTTP 200 OK response."""
        req.send_response(200)
        req.end_headers()
        raise RequestDone

