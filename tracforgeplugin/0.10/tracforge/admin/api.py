from trac.core import *
from trac.env import IEnvironmentSetupParticipant

class IProjectSetupParticipant(Interface):
    """An extension-point interface for performing actions on project creation."""
    
    def get_project_setup_actions(self):
        """Return an iterable of (name, type), where type is one of 'create' 
        or 'configure'. All configuration actions will always take place after 
        all creation tasks."""
        
    def perform_project_setup_action(self, req, env, action):
        """Perform the given setup action on an environment."""
    
class IProjectChangeListener(Interface):
    """An extension-point interface for performing actions on project changes."""
    pass # TODO: Implement this
    
class ProjectAdminSystem(Component):
    """Central stuff for tracforge.admin."""
    
    implements(IEnvironmentSetupParticipant)

    pass # TODO: Database setup goes here
