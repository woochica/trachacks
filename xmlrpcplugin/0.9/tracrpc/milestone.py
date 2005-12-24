from trac.core import *
from tracrpc.api import IXMLRPCHandler
import trac.ticket.model as model

class MilestoneRPC(Component):
    """ Interface to ticket milestones. """
    implements(IXMLRPCHandler)

    # IXMLRPCHandler methods
    def xmlrpc_procedures(self):
        yield ('TICKET_VIEW', self.listMilestones)

    def xmlrpc_namespace(self):
        return 'milestone'

    # Implementation
    def listMilestones(self):
        """ Get a list of milestones in the form (name, due, completed, description). """
        for milestone in model.Milestone.select(self.env):
            yield (milestone.name, milestone.due, milestone.completed, milestone.description)
