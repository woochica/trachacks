"""
AutoQuery - Plugin for trac 0.11
displays links to queries for items in the ticket badge
"""

import urllib

from trac.core import *
from trac.config import Option
from trac.web import IRequestFilter
from trac.web.chrome import ITemplateProvider

class AutoqueryPlugin(Component):
    implements(IRequestFilter, ITemplateProvider)

    query_args = Option('autoquery', 'query_args', default='&order=priority',
                        doc="additional arguments to the query string")


    ### methods for ITemplateProvider

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return []

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    ### methods for IRequestFilter

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """
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
        if template == 'ticket.html':
            query = self.env.href() + '/query?%s=%s' + self.query_args
            data['query_link'] = lambda x, y: query % (x, urllib.quote_plus(y))
            template = 'autoquery_ticket.html'
        return (template, data, content_type)
