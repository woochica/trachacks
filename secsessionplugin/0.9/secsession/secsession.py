from trac.core import *
from trac.web import IRequestHandler

class SecureSession(Component):
    implements(IRequestHandler)

    # IRequestHandler methods
    def match_request(self, req):
        # We want to handle all sessions that use http:// and have an 
        # authenticated user
        self.log.info("setting up the match")
        match = False
        if req.scheme == 'http':
            match = req.authname != 'anonymous'
            pass
        return match

    def process_request(self, req):
        self.log.info("redirect to secure site")
        secport = self.config.get('secsession', 'secport', 443)
        port = ''
        if secport != 443:
            port = ':%s' % str(secport)
            pass
        req.send_response(302)
        req.send_header('Location', ''.join(['https://',
                                            req.server_name,
                                            port,
                                            req.req.unparsed_uri,
                                           ]) )
        req.end_headers()
        #req.write('Hello world!')
