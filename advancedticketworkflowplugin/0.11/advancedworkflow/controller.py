"""Trac plugin that provides a number of advanced operations for customizable
workflows.
"""

from genshi.builder import tag

from trac.core import implements, Component
from trac.ticket import model
from trac.ticket.api import ITicketActionController
from trac.ticket.default_workflow import ConfigurableTicketWorkflow

# TODO:
#    set_owner_to_previous
#    run_external


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
