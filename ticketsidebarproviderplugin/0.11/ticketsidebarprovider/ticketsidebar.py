"""
TicketSidebarProvider
a plugin for Trac to provide content alongside the ticket
http://trac.edgewall.org/wiki/TracTicketsCustomFields
"""

from genshi.builder import tag
from genshi.filters import Transformer
from pkg_resources import resource_filename

from trac.config import Option
from trac.core import *
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_stylesheet
from trac.web.chrome import ITemplateProvider

from ticketsidebarprovider.interface import ITicketSidebarProvider


class TicketSidebarProvider(Component):

    implements(ITemplateStreamFilter, ITemplateProvider)

    providers = ExtensionPoint(ITicketSidebarProvider)

    ### method for ITemplateStreamFilter : 
    ### Filter a Genshi event stream prior to rendering.

    def filter_stream(self, req, method, filename, stream, data):
        """Return a filtered Genshi event stream, or the original unfiltered
        stream if no match.

        `req` is the current request object, `method` is the Genshi render
        method (xml, xhtml or text), `filename` is the filename of the template
        to be rendered, `stream` is the event stream and `data` is the data for
        the current template.

        See the Genshi documentation for more information.
        """

        if filename != 'ticket.html':
            return stream

        ticket = data['ticket']
        for provider in self.providers: # TODO : sorting
            if provider.enabled(req, ticket):
                add_stylesheet(req, 'common/css/ticket-sidebar.css')
                filter = Transformer('//div[@id="content"]')
                stream |= filter.after(tag.div(provider.content(req, ticket),
                                               **{'class': "sidebar" }))
        return stream

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return [('common', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        return []
