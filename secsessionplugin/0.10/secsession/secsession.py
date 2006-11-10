# Code wonderfully provided by csabahenk
from trac.core import *
from trac.web import IRequestFilter

__all__ = ['SecureSessionFilter']

class SecureSessionFilter(Component):
    implements(IRequestFilter)

    def pre_process_request(self, req, handler):
        # self.log.info("setting up the match")  ### 'twas too much noize

        # We provide a config hook for checking if the request is
        # secure. Simply checking the scheme is not the appropriate
        # choice in all case -- eg., if trac runs behind a proxy
        # server, then it will get simple http requests from the
        # proxy and we have to analyze headers to find out if
        # the original request was secure or not.
        #
        # Currently we can directly match a request attribute
        # as "@<attr> = <val>" or a http header line as "<hdlr> = <val>".
        # This could be generalized by, eg., taking a list of such
        # patterns, whatever.
        key, val = [ x.strip() for x in self.config.get('secsession',
                                                        'secpattern',
                                                        '@scheme=https'
                                                        ).split('=', 1) ]
        if key[0] == '@':
            myval = getattr(req, key[1:])
        else:
            myval = req.get_header(key)

        if unicode(myval) != val:
            # Auth info is not available at the time of invoking filters,
            # so we can't yet make the decision about redirecting.
            #
            # Therefore we just wrap the handler into our redirection policy.
            # When the handler will be invoked, auth info will be there;
            # if auth is anon, our wrapper will call the original
            # handler, else it will perform the redirect.
            handler = SecureSessionWrapper(handler, self)
        return handler

    def post_process_request(self, req, template, content_type):
        return template, content_type


class SecureSessionWrapper(object):

    def __init__(self, in_handler, filter):
        self.in_handler = in_handler
        self.config = filter.config
        self.log = in_handler.log

    def process_request(self, req):

        if not req.authname or req.authname == 'anonymous':
            return self.in_handler.process_request(req)

        self.log.info("redirect to secure site:")
        secport = self.config.getint('secsession', 'secport', 443)
        port = ''
        if secport != 443:
            port = ':%d' % secport

        req.redirect(''.join(['https://',
                              req.server_name,
                              port,
                              req.href(),
                              req.path_info
                              ]) )

