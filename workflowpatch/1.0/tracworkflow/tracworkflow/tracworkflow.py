# TracWorkFlow plugin

from trac.core import *
from trac.util import escape, Markup
from trac.ticket.api import ITicketActionController, FormControl
from track.ticket import model
from trac.env import IEnvironmentSetupParticipant

class TracWorkFlowPlugin(Component):
    implements(ITicketActionController, IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.upgrade_environment(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        verified = model.Status(self.env, db = db, name = 'verified')
        return not verified.exists

    def upgrade_environment(self, db):
        # Add ticket statuses
        for name in ('verified', 'reopened', 'resolved'):
            status = model.Status(self.env, db = db, name = name)
            status.insert(db)

    # ITicketActionController methods
    def get_ticket_actions(self, req, ticket):
        actions = {
            'new':      ['leave', 'resolve', 'reassign', 'accept', 'reopen', 'retest'],
            'assigned': ['leave', 'resolve', 'reassign', 'accept', 'reopen', 'retest'],
            'reopened': ['leave', 'resolve', 'reassign', 'accept', 'reopen', 'retest'],
            'closed':   ['leave', 'resolve', 'reassign', 'accept', 'reopen', 'retest'],
            'verified': ['leave', 'resolve', 'reassign', 'accept', 'reopen', 'retest'],
            'reopened': ['leave', 'resolve', 'reassign', 'accept', 'reopen', 'retest'],
            'resolved': ['leave', 'resolve', 'reassign', 'accept', 'reopen', 'retest'],
        }
        return actions[ticket['status']]

    def get_ticket_action_controls(self, req, ticket, action):
        """ Return HTML control for performing action on ticket. """
        controls = {
        }
        return controls[action]

    def apply_ticket_action(self, req, ticket, action):
        """ Perform action on ticket. """

    # Internal methods
    def new_controls(self, req, ticket):
        pass
