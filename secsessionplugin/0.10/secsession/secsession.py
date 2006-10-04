from trac.core import *
from trac.web.api import IRequestHandler, IRequestFilter
from urlparse import urlparse, urlunparse

__all__ = ['SecureSession', 'SecureSessionFilter']

class SecureSession(Component):
    implements(IRequestHandler)

    # IRequestHandler methods
    def match_request(self, req):
        # Never match anything by ourselves
        return False

    def process_request(self, req):
        orig_uri = req._reconstruct_url()
        self.log.debug('orig_uri: %s' % orig_uri)
        uri_parsed = urlparse(orig_uri)
        self.log.debug('uri_parsed: %s' % str(uri_parsed))
        uri_port = uri_parsed[1].split(':')
        self.log.debug('uri_port: %s' % str(uri_port))
        if len(uri_port) > 1:
            uri_port = uri_port[1]
        else:
            uri_port = None
        host = uri_parsed[1].split(':')[0]
        self.log.debug("host: %s" % str(host))
        path = uri_parsed[2]
        self.log.debug("path: %s" % str(path))
        parameters = uri_parsed[3]
        self.log.debug("parameters: %s" % str(parameters))
        query = uri_parsed[4]
        self.log.debug("query: %s" % str(query))
        fragment = uri_parsed[5]
        self.log.debug("fragment: %s" % str(fragment))
        
        secport = self.config.get('secsession', 'secport', 443)
        if secport != 443:
            host = '%s:%s' % (host, str(secport))
        elif uri_port:
            host = host.split(':')[0]
       
        uri = urlunparse(('https', host, path, parameters, query, fragment))
        self.log.debug("Location: %s" % uri)
        req.send_response(302)
        req.send_header('Location', uri)
        req.end_headers()


class SecureSessionFilter(Component):
    """ Filter to lock authenticated requests to https:// """

    implements(IRequestFilter)

    def pre_process_request(self, req, handler):
        # We want to handle all sessions that use http:// and have an 
        # authenticated user
        if req.scheme == 'http':
            match = req.authname != 'anonymous'
            handler = SecureSession(self.env)
            pass
        return handler

    def post_process_request(self, req, template, content_type):
        return (template, content_type)
