from paste.deploy import loadapp
from paste.deploy.converters import asbool

import re
import urlparse

from trac.config import *
from trac.core import *
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


class WSGITrac:
    """Callable class. Initi with path=/path/to/trac/env"""
    def __init__(self, path, secure=False, parent=False):
      self.path = path
      self.secure = secure
      self.parent = parent
    def __call__(self, environ, start_response):
      if self.parent:
        environ['trac.env_parent_dir'] = self.path
      else:
        environ['trac.env_path'] = self.path
      
      https = environ.get("HTTPS", "off")
      if self.secure and https != 'on':
        return redirect_https(environ, start_response)

      return dispatch_request(environ, start_response)


def redirect_https(environ, start_response):
	url = reconstruct_url(environ)
	s=list(urlparse.urlsplit(url))
	s[0]="https"
	u2 = urlparse.urlunsplit(s)
	start_response("302 Temporary Redirect", [('location', u2), ('content-type', 'text/plain')])
	return [u2]

def reconstruct_url(environ):
	from urllib import quote
	url = environ['wsgi.url_scheme']+'://'
	
	if environ.get('HTTP_HOST'):
		url += environ['HTTP_HOST']
	else:
		url += environ['SERVER_NAME']

		if environ['wsgi.url_scheme'] == 'https':
			if environ['SERVER_PORT'] != '443':
				url += ':' + environ['SERVER_PORT']
		else:
			if environ['SERVER_PORT'] != '80':
				url += ':' + environ['SERVER_PORT']
	url += quote(environ.get('SCRIPT_NAME',''))
	url += quote(environ.get('PATH_INFO',''))
	if environ.get('QUERY_STRING'):
		url += '?' + environ['QUERY_STRING']
	return url

                        
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
                                                                                                                        