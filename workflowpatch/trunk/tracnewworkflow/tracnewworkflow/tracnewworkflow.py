# TracWorkFlow plugin

from trac.core import *
from trac.util import escape, Markup
from trac.perm import IPermissionRequestor
from trac.ticket.api import ITicketWorkflow, \
                            DefaultTicketWorkflow, \
                            TicketSystem
from trac.ticket.field import *
from trac.ticket import model
from trac.env import IEnvironmentSetupParticipant
try:
    set()
except:
    from sets import Set as set

class NewWorkflowPlugin(Component):
    implements(ITicketWorkflow, IEnvironmentSetupParticipant,
        IPermissionRequestor)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'ROLE_QA'
        yield 'ROLE_DEVELOPER'
        yield 'ROLE_RELEASE'

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.upgrade_environment(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        try:
            verified = model.Status(self.env, db = db, name = 'verified')
            # XXX Example for using custom ticket fields
            #return not [1 for field in TicketSystem(self.env).get_custom_fields() if field['name'] == 'verify']
        except:
            return True
        return False

    def upgrade_environment(self, db):
        # Add ticket statuses
        for name in ('verified', 'resolved'):
            status = model.Status(self.env, db = db)
            status.name = name
            status.insert(db)
        #  XXX Example of how to add hidden custom ticket fields for use
        # in both workflow forms, and queries XXX
#        ticket_system = TicketSystem(self.env)
#        ticket_system.add_custom_field(Select('verify', skip=1,
#                                       options=('valid', 'irrelevant')))

    # ITicketWorkflow methods
    def get_ticket_actions(self, req, ticket):
        """ Given a ticket state, return the applicable actions. """
        actions = {'new':      ('leave', 'resolve', 'reassign', 'accept',                                      ),
                   'assigned': ('leave', 'resolve', 'reassign',                                                ),
                   'reopened': ('leave', 'resolve', 'reassign',                                                ),
                   'resolved': ('leave',            'reassign',           'reopen',           'verify'         ),
                   'verified': ('leave',            'reassign',           'reopen', 'retest',           'close'),
                   'closed':   ('leave',                                  'reopen', 'retest',                  )}

        # Permissions required to perform actions.
        perms = {'resolve':  {'allof': ('TICKET_MODIFY',),
                              'anyof': ('ROLE_DEVELOPER',)},
                 'reassign': {'allof': ('TICKET_CHGPROP',),
                              'anyof': ('ROLE_DEVELOPER', 'ROLE_QA',
                                        'ROLE_RELEASE')},
                 'accept':   {'allof': ('TICKET_CHGPROP',),
                              'anyof': ('ROLE_DEVELOPER',)},
                 'reopen':   {'allof': ('TICKET_CREATE',),
                              'anyof': ('ROLE_QA',)},
                 'verify':   {'allof': ('TICKET_CHGPROP',),
                              'anyof': ('ROLE_QA',)},
                 'retest':   {'allof': ('ROLE_RELEASE',)},
                 'close':    {'allof': ('TICKET_CHGPROP',),
                              'anyof': ('ROLE_QA', 'ROLE_RELEASE')}}

        # Filter available actions for ticket status, based on user permissions
        filtered = []
        for action in actions.get(ticket['status'], ['leave']):
            if action not in perms:
                filtered.append(action)
            else:
                allof = set(perms[action].get('allof', ()))
                anyof = set(perms[action].get('anyof', ()))
                have = set([perm for perm in allof.union(anyof)
                            if req.perm.has_permission(perm)])

                if (not allof or allof.intersection(have) == allof) and \
                        (not anyof or anyof.intersection(have)):
                    filtered.append(action)

        return filtered

    def get_ticket_action_controls(self, req, ticket, action):
        # Use default workflow for leave, resolve, reassign, reopen and accept
        if action in ('leave', 'resolve', 'reassign', 'reopen', 'accept'):
            return DefaultTicketWorkflow(self.env) \
                   .get_ticket_action_controls(req, ticket, action)
        return {
            'retest': {},
            'verify': {},
            'close': {},
            # XXX Example of using custom ticket fields
#            'verify': Select('verify_reason', label = 'as:',
#                             options = ['valid', 'irrelevant']),
        }[action]

    def apply_ticket_action(self, req, ticket, action):
        """ Perform action on ticket. """

        status = {'accept': 'assigned',
                  'resolve': 'resolved',
                  'reassign': 'new',
                  'reopen': 'reopened',
                  'retest': 'resolved',
                  'verify': 'verified',
                  'close': 'closed'}

        if action == 'leave': return

        ticket['status'] = status[action]

        if action == 'accept':
            ticket['owner'] = req.authname
        elif action == 'resolve':
            ticket['resolution'] = req.args.get('resolve_resolution')
        elif action == 'reassign':
            ticket['owner'] = req.args.get('reassign_owner')
        elif action == 'reopen':
            ticket['resolution'] = ''
        # XXX Example of using custom ticket fields
#        elif action == 'verify':
#            ticket['verify'] = req.args.get('verify_reason')
