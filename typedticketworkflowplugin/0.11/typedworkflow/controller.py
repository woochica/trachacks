from trac.core import implements, Component
from trac.ticket import model
from trac.ticket.api import ITicketActionController
from trac.ticket.default_workflow import ConfigurableTicketWorkflow


class TypedTicketWorkflow(ConfigurableTicketWorkflow):
    """Add type attribute filter """
    
    def get_ticket_actions(self, req, ticket):        
        actions =  ConfigurableTicketWorkflow.get_ticket_actions(self, req, ticket)        
        actions = self.filter_actions(actions, ticket)
        return actions
    
    def filter_actions(self, action, ticket):
        """Finds the actions that use this operation"""
        filterd_actions = []        
        for default, action_name in action:
            action_attributes = self.actions[action_name]
            if 'tickettype' in action_attributes:
                #TODO normalization this should be done only once                
                required_types = [a.strip() for a in 
                                  action_attributes['tickettype'].split(',')]
                if ticket.get_value_or_default('type') in required_types:
                    filterd_actions.append((default, action_name))
            else:
                filterd_actions.append((default, action_name))                
        return filterd_actions