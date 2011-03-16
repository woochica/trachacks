"""Trac plugin that provides a number of advanced operations for customizable
workflows.
"""

import os
import time
from datetime import datetime
from subprocess import call
from genshi.builder import tag

from trac.core import implements, Component
from trac.ticket import model
from trac.ticket.api import ITicketActionController
from trac.ticket.default_workflow import ConfigurableTicketWorkflow
from trac.ticket.model import Milestone
from trac.ticket.notification import TicketNotifyEmail
from trac.resource import ResourceNotFound
from trac.util.datefmt import utc
from trac.web.chrome import add_warning


class TicketWorkflowOpBase(Component):
    """Abstract base class for 'simple' ticket workflow operations."""

    implements(ITicketActionController)
    abstract = True

    _op_name = None # Must be specified.

    # ITicketActionController methods

    def get_ticket_actions(self, req, ticket):
        """Finds the actions that use this operation"""
        controller = ConfigurableTicketWorkflow(self.env)
        return controller.get_actions_by_operation_for_req(req, ticket,
                                                           self._op_name)

    def get_all_status(self):
        """Provide any additional status values"""
        # We don't have anything special here; the statuses will be recognized
        # by the default controller.
        return []

    # This should most likely be overridden to be more functional
    def render_ticket_action_control(self, req, ticket, action):
        """Returns the action control"""
        actions = ConfigurableTicketWorkflow(self.env).actions
        label = actions[action]['name']
        return (label, tag(''), '')

    def get_ticket_changes(self, req, ticket, action):
        """Must be implemented in subclasses"""
        raise NotImplementedError

    def apply_action_side_effects(self, req, ticket, action):
        """No side effects"""
        pass


class TicketWorkflowOpOwnerReporter(TicketWorkflowOpBase):
    """Sets the owner to the reporter of the ticket.

    needinfo = * -> needinfo
    needinfo.name = Need info
    needinfo.operations = set_owner_to_reporter


    Don't forget to add the `TicketWorkflowOpOwnerReporter` to the workflow
    option in [ticket].
    If there is no workflow option, the line will look like this:

    workflow = ConfigurableTicketWorkflow,TicketWorkflowOpOwnerReporter
    """

    _op_name = 'set_owner_to_reporter'

    # ITicketActionController methods

    def render_ticket_action_control(self, req, ticket, action):
        """Returns the action control"""
        actions = ConfigurableTicketWorkflow(self.env).actions
        label = actions[action]['name']
        hint = 'The owner will change to %s' % ticket['reporter']
        control = tag('')
        return (label, control, hint)

    def get_ticket_changes(self, req, ticket, action):
        """Returns the change of owner."""
        return {'owner': ticket['reporter']}


class TicketWorkflowOpOwnerComponent(TicketWorkflowOpBase):
    """Sets the owner to the default owner for the component.

    <someaction>.operations = set_owner_to_component_owner

    Don't forget to add the `TicketWorkflowOpOwnerComponent` to the workflow
    option in [ticket].
    If there is no workflow option, the line will look like this:

    workflow = ConfigurableTicketWorkflow,TicketWorkflowOpOwnerComponent
    """

    _op_name = 'set_owner_to_component_owner'

    # ITicketActionController methods

    def render_ticket_action_control(self, req, ticket, action):
        """Returns the action control"""
        actions = ConfigurableTicketWorkflow(self.env).actions
        label = actions[action]['name']
        hint = 'The owner will change to %s' % self._new_owner(ticket)
        control = tag('')
        return (label, control, hint)

    def get_ticket_changes(self, req, ticket, action):
        """Returns the change of owner."""
        return {'owner': self._new_owner(ticket)}

    def _new_owner(self, ticket):
        """Determines the new owner"""
        component = model.Component(self.env, name=ticket['component'])
        self.env.log.debug("component %s, owner %s" % (component, component.owner))
        return component.owner


class TicketWorkflowOpOwnerField(TicketWorkflowOpBase):
    """Sets the owner to the value of a ticket field

    <someaction>.operations = set_owner_to_field
    <someaction>.set_owner_to_field = myfield

    Don't forget to add the `TicketWorkflowOpOwnerField` to the workflow
    option in [ticket].
    If there is no workflow option, the line will look like this:

    workflow = ConfigurableTicketWorkflow,TicketWorkflowOpOwnerField
    """

    _op_name = 'set_owner_to_field'

    # ITicketActionController methods

    def render_ticket_action_control(self, req, ticket, action):
        """Returns the action control"""
        actions = ConfigurableTicketWorkflow(self.env).actions
        label = actions[action]['name']
        hint = 'The owner will change to %s' % self._new_owner(action, ticket)
        control = tag('')
        return (label, control, hint)

    def get_ticket_changes(self, req, ticket, action):
        """Returns the change of owner."""
        return {'owner': self._new_owner(action, ticket)}

    def _new_owner(self, action, ticket):
        """Determines the new owner"""
        # Should probably do some sanity checking...
        field = self.config.get('ticket-workflow',
                                action + '.' + self._op_name).strip()
        return ticket[field]


class TicketWorkflowOpOwnerPrevious(TicketWorkflowOpBase):
    """Sets the owner to the previous owner

    Don't forget to add the `TicketWorkflowOpOwnerPrevious` to the workflow
    option in [ticket].
    If there is no workflow option, the line will look like this:

    workflow = ConfigurableTicketWorkflow,TicketWorkflowOpOwnerPrevious
    """

    _op_name = 'set_owner_to_previous'

    # ITicketActionController methods

    def render_ticket_action_control(self, req, ticket, action):
        """Returns the action control"""
        actions = ConfigurableTicketWorkflow(self.env).actions
        label = actions[action]['name']
        new_owner = self._new_owner(ticket)
        if new_owner:
            hint = 'The owner will change to %s' % new_owner
        else:
            hint = 'The owner will be deleted.'
        control = tag('')
        return (label, control, hint)

    def get_ticket_changes(self, req, ticket, action):
        """Returns the change of owner."""
        return {'owner': self._new_owner(ticket)}

    def _new_owner(self, ticket):
        """Determines the new owner"""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT oldvalue FROM ticket_change WHERE ticket=%s " \
                       "AND field='owner' ORDER BY -time", (ticket.id, ))
        row = cursor.fetchone()
        if row:
            owner = row[0]
        else: # The owner has never changed.
            owner = ''
        return owner


class TicketWorkflowOpStatusPrevious(TicketWorkflowOpBase):
    """Sets the status to the previous status

    Don't forget to add the `TicketWorkflowOpStatusPrevious` to the workflow
    option in [ticket].
    If there is no workflow option, the line will look like this:

    workflow = ConfigurableTicketWorkflow,TicketWorkflowOpStatusPrevious
    """

    _op_name = 'set_status_to_previous'

    # ITicketActionController methods

    def render_ticket_action_control(self, req, ticket, action):
        """Returns the action control"""
        actions = ConfigurableTicketWorkflow(self.env).actions
        label = actions[action]['name']
        new_status = self._new_status(ticket)
        if new_status != self._old_status(ticket):
            hint = 'The status will change to %s' % new_status
        else:
            hint = ''
        control = tag('')
        return (label, control, hint)

    def get_ticket_changes(self, req, ticket, action):
        """Returns the change of status."""
        return {'status': self._new_status(ticket)}

    def _old_status(self, ticket):
        """Determines what the ticket state was (is)"""
        return ticket._old.get('status', ticket['status'])

    def _new_status(self, ticket):
        """Determines the new status"""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT oldvalue FROM ticket_change WHERE ticket=%s " \
                       "AND field='status' ORDER BY -time", (ticket.id, ))
        row = cursor.fetchone()
        if row:
            status = row[0]
        else: # The status has never changed.
            status = 'new'
        return status


class TicketWorkflowOpRunExternal(Component):
    """Action to allow running an external command as a side-effect.

    If it is a lengthy task, it should daemonize so the webserver can get back
    to doing its thing.  If the script exits with a non-zero return code, an
    error will be logged to the Trac log.
    The plugin will look for a script named <tracenv>/hooks/<someaction>, and
    will pass it 2 parameters: the ticket number, and the user.

    <someaction>.operations = run_external
    <someaction>.run_external = Hint for the user

    Don't forget to add the `TicketWorkflowOpRunExternal` to the workflow
    option in [ticket].
    If there is no workflow option, the line will look like this:

    workflow = ConfigurableTicketWorkflow,TicketWorkflowOpRunExternal
    """

    implements(ITicketActionController)

    # ITicketActionController methods

    def get_ticket_actions(self, req, ticket):
        """Finds the actions that use this operation"""
        controller = ConfigurableTicketWorkflow(self.env)
        return controller.get_actions_by_operation_for_req(req, ticket,
                                                           'run_external')

    def get_all_status(self):
        """Provide any additional status values"""
        # We don't have anything special here; the statuses will be recognized
        # by the default controller.
        return []

    def render_ticket_action_control(self, req, ticket, action):
        """Returns the action control"""
        actions = ConfigurableTicketWorkflow(self.env).actions
        label = actions[action]['name']
        hint = self.config.get('ticket-workflow',
                               action + '.run_external').strip()
        if hint is None:
            hint = "Will run external script."
        return (label, tag(''), hint)

    def get_ticket_changes(self, req, ticket, action):
        """No changes to the ticket"""
        return {}

    def apply_action_side_effects(self, req, ticket, action):
        """Run the external script"""
        print "running external script for %s" % action
        script = os.path.join(self.env.path, 'hooks', action)
        for extension in ('', '.exe', '.cmd', '.bat'):
            if os.path.exists(script + extension):
                script += extension
                break
        else:
            self.env.log.error("Error in ticket workflow config; could not find external command to run for %s in %s" % (action, os.path.join(self.env.path, 'hooks')))
            return
        retval = call([script, str(ticket.id), req.authname])
        if retval:
            self.env.log.error("External script %r exited with return code %s." % (script, retval))


class TicketWorkflowOpTriage(TicketWorkflowOpBase):
    """Action to split a workflow based on a field

    <someaction> = somestatus -> *
    <someaction>.operations = triage
    <someaction>.triage_field = type
    <someaction>.traige_split = defect -> new_defect, task -> new_task, enhancement -> new_enhancement

    Don't forget to add the `TicketWorkflowOpTriage` to the workflow option in
    [ticket].
    If there is no workflow option, the line will look like this:

    workflow = ConfigurableTicketWorkflow,TicketWorkflowOpTriage
    """

    _op_name = 'triage'

    # ITicketActionController methods

    def render_ticket_action_control(self, req, ticket, action):
        """Returns the action control"""
        actions = ConfigurableTicketWorkflow(self.env).actions
        label = actions[action]['name']
        new_status = self._new_status(ticket, action)
        if new_status != ticket['status']:
            hint = 'The status will change to %s.' % new_status
        else:
            hint = ''
        control = tag('')
        return (label, control, hint)

    def get_ticket_changes(self, req, ticket, action):
        """Returns the change of status."""
        return {'status': self._new_status(ticket, action)}

    def _new_status(self, ticket, action):
        """Determines the new status"""
        field = self.config.get('ticket-workflow',
                                action + '.triage_field').strip()
        transitions = self.config.get('ticket-workflow',
                                      action + '.triage_split').strip()
        for transition in [x.strip() for x in transitions.split(',')]:
            value, status = [y.strip() for y in transition.split('->')]
            if value == ticket[field].strip():
                break
        else:
            self.env.log.error("Bad configuration for 'triage' operation in action '%s'" % action)
            status = 'new'
        return status


class TicketWorkflowOpXRef(TicketWorkflowOpBase):
    """Adds a cross reference to another ticket

    <someaction>.operations = xref
    <someaction>.xref = "Ticket %s is related to this ticket"
    <someaction>.xref_local = "Ticket %s was marked as related to this ticket"
    <someaction>.xref_hint = "The specified ticket will be cross-referenced with this ticket"

    The example values shown are the default values.
    Don't forget to add the `TicketWorkflowOpXRef` to the workflow
    option in [ticket].
    If there is no workflow option, the line will look like this:

    workflow = ConfigurableTicketWorkflow,TicketWorkflowOpXRef
    """

    _op_name = 'xref'

    # ITicketActionController methods

    def render_ticket_action_control(self, req, ticket, action):
        """Returns the action control"""
        id = 'action_%s_xref' % action
        ticketnum = req.args.get(id, '')
        actions = ConfigurableTicketWorkflow(self.env).actions
        label = actions[action]['name']
        hint = actions[action].get('xref_hint',
            'The specified ticket will be cross-referenced with this ticket')
        control = tag.input(type='text', id=id, name=id, value=ticketnum)
        return (label, control, hint)

    def get_ticket_changes(self, req, ticket, action):
        # WARNING: Directly modifying the ticket in this method breaks the
        # intent of this method.  But it does accomplish the desired goal.
        if not 'preview' in req.args:
            id = 'action_%s_xref' % action
            ticketnum = req.args.get(id).strip('#')

            try:
                xticket = model.Ticket(self.env, ticketnum)
            except ResourceNotFound, e:
                #put in preview mode to prevent ticket being saved
                req.args['preview'] = True
                add_warning(req, "Unable to cross-reference Ticket #%s (%s)." % (ticketnum, e.message))
                return {}

            oldcomment = req.args.get('comment')
            actions = ConfigurableTicketWorkflow(self.env).actions
            format_string = actions[action].get('xref_local',
                'Ticket %s was marked as related to this ticket')
            # Add a comment to this ticket to indicate that the "remote" ticket is
            # related to it.  (But only if <action>.xref_local was set in the
            # config.)
            if format_string:
                comment = format_string % ('#%s' % ticketnum)
                req.args['comment'] = "%s%s%s" % \
                    (comment, oldcomment and "[[BR]]" or "", oldcomment or "")

        """Returns no changes."""
        return {}

    def apply_action_side_effects(self, req, ticket, action):
        """Add a cross-reference comment to the other ticket"""
        # TODO: This needs a lot more error checking.
        id = 'action_%s_xref' % action
        ticketnum = req.args.get(id).strip('#')
        actions = ConfigurableTicketWorkflow(self.env).actions
        author = req.authname

        # Add a comment to the "remote" ticket to indicate this ticket is
        # related to it.
        format_string = actions[action].get('xref',
                                        'Ticket %s is related to this ticket')
        comment = format_string % ('#%s' % ticket.id)
        # FIXME: we need a cnum to avoid messing up 
        xticket = model.Ticket(self.env, ticketnum)
        # FIXME: We _assume_ we have sufficient permissions to comment on the
        # other ticket.
        now = datetime.now(utc)
        xticket.save_changes(author, comment, now)

        #Send notification on the other ticket
        try:
            tn = TicketNotifyEmail(self.env)
            tn.notify(xticket, newticket=False, modtime=now)
        except Exception, e:
            self.log.exception("Failure sending notification on change to "
                               "ticket #%s: %s" % (ticketnum, e))


class TicketWorkflowOpResetMilestone(TicketWorkflowOpBase):
    """Resets the ticket milestone if it is assigned to a completed milestone.
    This is useful for reopen operations.

    reopened = closed -> reopened
    reopened.name = Reopened
    reopened.operations = reset_milestone


    Don't forget to add the `TicketWorkflowOpResetMilestone` to the  workflow
    option in [ticket].
    If there is no workflow option, the line will look like this:

    workflow =  ConfigurableTicketWorkflow,TicketWorkflowOpResetMilestone
    """

    _op_name = 'reset_milestone'

    # ITicketActionController methods

    def render_ticket_action_control(self, req, ticket, action):
        """Returns the action control"""
        actions = ConfigurableTicketWorkflow(self.env).actions
        label = actions[action]['name']
        # check if the assigned milestone has been completed
        milestone = Milestone(self.env,ticket['milestone'])
        if milestone.is_completed:
            hint = 'The milestone will be reset'
        else:
            hint = ''
        control = tag('')
        return (label, control, hint)

    def get_ticket_changes(self, req, ticket, action):
        """Returns the change of milestone, if needed."""
        milestone = Milestone(self.env,ticket['milestone'])
        if milestone.is_completed:
            return {'milestone': ''}
        return {}
