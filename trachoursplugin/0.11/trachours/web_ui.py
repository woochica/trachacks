"""
sidebar for inputting hours
"""

from componentdependencies.interface import IRequireComponents
from hours import TracHoursPlugin
from ticketsidebarprovider.interface import ITicketSidebarProvider
from ticketsidebarprovider.ticketsidebar import TicketSidebarProvider
from trac.core import *
from trac.web.chrome import Chrome
from trac.web.chrome import ITemplateProvider

class TracHoursSidebarProvider(Component):

    implements(ITicketSidebarProvider, IRequireComponents)

    ### methods for IRequireComponents

    def requires(self):
        return [TracHoursPlugin, TicketSidebarProvider]


    ### methods for ITicketSidebarProvider

    def enabled(self, req, ticket):
        if ticket.id and req.authname and 'TICKET_ADD_HOURS' in req.perm:
            return True
        return False

    def content(self, req, ticket):
        data = { 'worker': req.authname,
                 'action': req.href('hours', ticket.id) }
        return Chrome(self.env).load_template('hours_sidebar.html').generate(**data)


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
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
