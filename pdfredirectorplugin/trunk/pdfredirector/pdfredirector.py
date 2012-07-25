"""
PDFRedirector:
a plugin for Trac
http://trac.edgewall.org
"""

from trac.core import *

from trac.web.api import IRequestFilter

class PDFRedirector(Component):

    implements(IRequestFilter)

    ### methods for IRequestFilter

    """Extension point interface for components that want to filter HTTP
    requests, before and/or after they are processed by the main handler."""

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

        return template, data, content_type

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """
        path = req.path_info.strip('/').split('/')
        if len(path) < 2 or path[0] != 'attachment':
            return handler

        if not path[-1].lower().endswith('.pdf'):
            return handler

        filename = req.href(*(['raw-attachment'] + path[1:]))

        req.redirect(filename) 





