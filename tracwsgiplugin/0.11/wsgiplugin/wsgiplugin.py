from paste.deploy import loadapp
from paste.deploy.converters import asbool
from paste.request import construct_url, path_info_pop

import re
import urlparse
import os

from genshi.template.plugin import MarkupTemplateEnginePlugin
from trac.config import *
from trac.core import *
from trac.env import open_environment
from trac.perm import PermissionCache, PermissionSystem
from trac.web.api import IRequestHandler, RequestDone
from trac.web.main import dispatch_request

__all__ = ["WSGIPluginModule", "WSGITrac"]

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
        app = self.apps[path_info_pop(req.environ)]
        def my_start_response(status, headers, exc=None):
          req.send_response(int(status.split(" ")[0]))
          for key, value in headers:
            req.send_header(key, value)
          req.end_headers()
          
        appiter = app(req.environ, my_start_response)
        for chunk in appiter:
          req.write(chunk)
        raise RequestDone


class WSGITrac:
    """Callable class. Initi with path=/path/to/trac/env"""
    def __init__(self, path, secure=False, parent=False):
      self.path = path
      self.secure = secure
      self.parent = parent
      self.template = MarkupTemplateEnginePlugin()
    
    def __call__(self, environ, start_response):

      https = environ.get("HTTPS", "off")
      if self.secure and https != 'on':
        return redirect_https(environ, start_response)
    
      if self.parent:
        project = path_info_pop(environ)
        if project:
            environ['trac.env_path'] = os.path.join(self.path, project)
            return dispatch_request(environ, start_response)
        else:
            return self._send_index(environ, start_response)
          
      else:
        environ['trac.env_path'] = self.path
        return dispatch_request(environ, start_response)
            
        
    def _send_index(self, environ, start_response):
        projects = []
                          
        for env_name in os.listdir(self.path):
            env_path = os.path.join(self.path, env_name)
            try:
              env = _open_environment(env_path)
              env_perm = PermissionCache(PermissionSystem(env).get_user_permissions(environ.get("REMOTE_USER", "anonymous")))
                      
              if env_perm.has_permission('WIKI_VIEW'):
                  projects.append({
                      'name': env.project_name,
                      'description': env.project_description,
                      # XXX: get rid of the double / in the beginning
                      'href': construct_url(environ, path_info="/"+env_name),
                  })
            except Exception:
              pass

        projects.sort(lambda x, y: cmp(x['name'].lower(), y['name'].lower()))
        start_response("200 OK", [('content-type', 'text/html')])
        return self.template.render({"projects":projects}, format='xhtml', template = "wsgiplugin.index")
        

# XXX: This has nothing to do with Trac
def redirect_https(environ, start_response):
	url = construct_url(environ)
	s=list(urlparse.urlsplit(url))
	s[0]="https"
	u2 = urlparse.urlunsplit(s)
	start_response("302 Temporary Redirect", [('location', u2), ('content-type', 'text/plain')])
	return [u2]

                        
def wsgi_trac(global_conf, path = None, secure = False, **local_conf):
    return WSGITrac(path, secure=asbool(secure))

def wsgi_tracs(global_conf, path = None, secure = False, **local_conf):
    return WSGITrac(path, secure=asbool(secure), parent = True)


class Redirect():
  def __init__(self, url, code=302):
    self.url = url
    self.status = "%d Redirect" %(code)
  def __call__(self, environ, start_response):
    start_response(self.status, [('Location', self.url)])
    return []

def permanent_redirect(global_conf, url):
  return Redirect(url, 301)

def temporary_redirect(global_conf, url):	
  return Redirect(url, 302)
