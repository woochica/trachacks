from trac.core import *
from tracrpc.api import IXMLRPCHandler
import trac.ticket.model as model

class ComponentRPC(Component):
    """ Interface to ticket components. """
    implements(IXMLRPCHandler)

    # IXMLRPCHandler methods
    def xmlrpc_procedures(self):
        yield ('TICKET_VIEW', self.listComponents)

    def xmlrpc_namespace(self):
        return 'component'

    # Implementation
    def listComponents(self):
        """ Get a list of components in the form (name, owner, description). """
        for component in model.Component.select(self.env):
            yield (component.name, component.owner, component.description)

