"""
Ticket sidebar for moving tickets
"""

from pkg_resources import resource_filename
from ticketmoverplugin.ticketmover import TicketMover
from ticketsidebarprovider import ITicketSidebarProvider
from trac.config import Option
from trac.core import *
from trac.web.api import IRequestHandler
from trac.web.chrome import Chrome, ITemplateProvider


class TicketMoverSidebar(Component):
    implements(ITicketSidebarProvider, ITemplateProvider)

    permission = Option('ticket', 'move_permission', 'TICKET_ADMIN',
                        "permission needed to move tickets between Trac projects")

    ### ITicketSidebarProvider methods

    def enabled(self, req, ticket):
        if not self.permission in req.perm or not ticket.exists:
            return False
        tm = TicketMover(self.env)
        projects = tm.projects(req.authname)
        return bool(projects)

    def content(self, req, ticket):
        tm = TicketMover(self.env)
        projects = tm.projects(req.authname)
        chrome = Chrome(self.env)
        template = chrome.load_template('ticketmover-sidebar.html')
        data = {'projects': projects,
                'req': req,
                'ticket': ticket}
        return template.generate(**data)


    ### ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]


class TicketMoverHandler(Component):
    permission = Option('ticket', 'move_permission', 'TICKET_ADMIN',
                        "permission needed to move tickets between Trac projects")

    implements(IRequestHandler)

    ### IRequestHandler methods

    def match_request(self, req):
        return req.method == 'POST' and req.path_info.rstrip('/') == '/ticket/move'

    def process_request(self, req):

        assert self.permission in req.perm

        tm = TicketMover(self.env)
        new_location = tm.move(req.args['ticket'], req.authname, req.args['project'], 'delete' in req.args)

        if 'delete' in req.args:
            req.redirect(new_location)
        else:
            req.redirect(req.href('/ticket/%s' % req.args['ticket']))

