from paste.deploy import loadapp

import re

from trac.config import *
from trac.core import *
from trac.web.api import IRequestHandler, RequestDone


class WSGIPluginModule(Component):
    """Handles WSGI subapps for Trac."""

    implements(IRequestHandler)

    def __init__(self):
      self.apps = {}
      # application specified in same trac.ini
      if hasattr(self, "config"):
      #self.app = loadapp("config:%s"%(self.config.filename))
        for key, value in self.config.options('webapps'):
          if value.find(":") == -1:
            self.apps[key] = loadapp("config:%s"%(self.config.filename), name=value)
          else:
            self.apps[key] = loadapp(value)
          
      self.pattern = '/(%s)/?'%("|".join(self.apps.keys()))
      
    # IRequestHandler methods
    def match_request(self, req):
        result = re.match(self.pattern, req.path_info)
        return result

    def process_request(self, req):
        # XXX: set SCRIPT_NAME and PATH_INFO as needed
        # print req.environ["SCRIPT_NAME"], req.environ["PATH_INFO"]
        # XXX: URLMap here maybe ?
        app = self.apps[req.environ["PATH_INFO"].strip("/").split("/")[0]]
        def my_start_response(status, headers, exc=None):
          req.send_response(int(status.split(" ")[0]))
          for key, value in headers:
            req.send_header(key, value)
          req.end_headers()
          
        appiter = app(req.environ, my_start_response)
        for chunk in appiter:
          req.write(chunk)
        raise RequestDone
