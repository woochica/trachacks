# Plugin for trac 0.11

import random
import sys
import time
import urllib

from genshi.builder import Markup
from genshi.builder import tag
from genshi.filters.transform import Transformer

from pkg_resources import resource_filename

from skimpyGimpy import skimpyAPI

from trac.core import *
from trac.web import IRequestFilter
from trac.web import ITemplateStreamFilter
from trac.web.api import IAuthenticator
from trac.web.chrome import add_warning 
from trac.web.chrome import ITemplateProvider
from trac.config import ListOption
from trac.config import Option

class AuthCaptcha(Component):

    ### class data
    implements(IRequestFilter, ITemplateStreamFilter, IAuthenticator, ITemplateProvider)
    dict_file = Option('captchaauth', 'dictionary_file',
                           default="http://java.sun.com/docs/books/tutorial/collections/interfaces/examples/dictionary.txt")
    captcha_type = Option('captchaauth', 'type',
                          default="png")
    realms = ListOption('captchaauth', 'realms',
                        default="wiki, newticket")

    permissions = { 'wiki': [ 'WIKI_CREATE', 'WIKI_MODIFY' ],
                    'newticket': [ 'TICKET_CREATE' ] }

    xpath = { 'ticket.html': "//div[@class='buttons']" }

    ### IRequestFilter methods

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """

        if req.method != 'GET':
            # TODO more here?
            return handler

        if req.perm.username != 'anonymous':
            return handler

        path = req.path_info.strip('/').split('/')
        if path:
            if path[0] in self.realms:
                pass

        return handler

    # for ClearSilver templates
    def post_process_request(self, req, template, content_type):
        """Do any post-processing the request might need; typically adding
        values to req.hdf, or changing template or mime type.
        
        Always returns a tuple of (template, content_type), even if
        unchanged.

        Note that `template`, `content_type` will be `None` if:
         - called when processing an error page
         - the default request handler did not return any result

        (for 0.10 compatibility; only used together with ClearSilver templates)
        """
        return (template, content_type)

    # for Genshi templates
    def post_process_request(self, req, template, data, content_type):
        """Do any post-processing the request might need; typically adding
        values to the template `data` dictionary, or changing template or
        mime type.
        
        `data` may be update in place.

        Always returns a tuple of (template, data, content_type), even if
        unchanged.

        Note that `template`, `data`, `content_type` will be `None` if:
         - called when processing an error page
         - the default request handler did not return any result

        (Since 0.11)
        """
        return (template, data, content_type)

    
    ### ITemplateStreamFilter method

    def filter_stream(self, req, method, filename, stream, data):
        """Return a filtered Genshi event stream, or the original unfiltered
        stream if no match.

        `req` is the current request object, `method` is the Genshi render
        method (xml, xhtml or text), `filename` is the filename of the template
        to be rendered, `stream` is the event stream and `data` is the data for
        the current template.

        See the Genshi documentation for more information.
        """
        if filename in self.xpath:
            xpath = self.xpath[filename]
#            stream |= Transformer(xpath).before(# XXX template)

        return stream

    ### methods for ITemplateProvider

    """Extension point interface for components that provide their own
    ClearSilver templates and accompanying static resources.
    """

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return []

    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        return [resource_filename(__name__, 'templates')]

    ### methods for IAuthenticator

    """Extension point interface for components that can provide the name
    of the remote user."""

    def authenticate(self, req):
        """Return the name of the remote user, or `None` if the identity of the
        user is unknown."""
        return None
        return 'foo' # XXX stub
