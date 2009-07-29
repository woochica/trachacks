"""
test class for ComponentDependencyPlugin
"""

from trac.core import *
from trac.web import IRequestHandler
from componentdependencies import IRequireComponents

__all__ = [ 'FooBarTest', 'TestDependencyPlugin', ]

class FooBarTest(Component):
    
    def foobar(self):
        return "hello world"

class TestDependencyPlugin(Component):

    implements(IRequestHandler, IRequireComponents)

    ### methods for IRequestHandler

    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        return req.path_info == '/hello-world'
        

    def process_request(self, req):
        """Process the request. For ClearSilver, return a (template_name,
        content_type) tuple, where `template` is the ClearSilver template to use
        (either a `neo_cs.CS` object, or the file name of the template), and
        `content_type` is the MIME type of the content. For Genshi, return a
        (template_name, data, content_type) tuple, where `data` is a dictionary
        of substitutions for the template.

        For both templating systems, "text/html" is assumed if `content_type` is
        `None`.

        Note that if template processing should not occur, this method can
        simply send the response itself and not return anything.
        """
        foobar = FooBarTest(self.env)
        req.send(foobar.foobar(), "text/plain")


    ### methods for IRequireComponents
        
    def requires(self):
        return [ FooBarTest ]
