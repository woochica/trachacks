from trac.core import *
from tracrpc.api import IXMLRPCHandler
import trac.ticket.model as model

class ComponentRPC(Component):
    """ Interface to ticket milestones. """
    implements(IXMLRPCHandler)

    # IXMLRPCHandler methods
    def get_xmlrpc_functions(self):
        yield ('TICKET_VIEW', self.get_milestones)

    # Implementation
    def get_milestones(self):
        """ Get a list of milestones in the form (name, due, completed, description). """
        for milestone in model.Milestone.select(self.env):
            yield (milestone.name, milestone.due, milestone.completed, milestone.description)
