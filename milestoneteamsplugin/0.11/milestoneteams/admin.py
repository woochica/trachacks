# Trac core imports
from trac.core import *
from trac.config import *

# Trac extension point imports
from trac.admin.api import IAdminPanelProvider

#class mtAdminPanel(Component):
#    """Modifies Trac UI for editing Milestone Teams"""
#    implements(IAdminPanelProvider)

#    def get_admin_panels(self, req):
#        """Return a list of our administration panels."""
#        return ('ticket', 'Ticket System', 'milestoneteams', ('Milestone Teams', 'Milestone Teams'))

#    def render_admin_panel(self, req, category, page, path_info):
#        """Return the template and data used to render our administration page."""
#        pass
