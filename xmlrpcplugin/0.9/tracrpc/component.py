from trac.core import *
from tracrpc.api import IXMLRPCHandler
import trac.ticket.model as model

class ComponentRPC(Component):
    """ Interface to ticket components. """
    implements(IXMLRPCHandler)

    # IXMLRPCHandler methods
    def get_xmlrpc_functions(self):
        yield ('TICKET_VIEW', self.get_components)

    # Implementation
    def get_components(self):
        """ Get a list of components in the form (name, owner, description). """
        for component in model.Component.select(self.env):
            yield (component.name, component.owner, component.description)

