# Trac core imports
from trac.core import *
from trac.config import *

# Trac extension point imports
from trac.env import IEnvironmentSetupParticipant

class mtSetupParticipant(Component):
    """Sets up Trac system for the Milestone Teams plugin."""
    implements(IEnvironmentSetupParticipant)
    
    def environment_created(self):
        """Peform setup tasks when the environment is first created."""

    def environment_needs_upgrade(self, db):
        """Check to see if the current environment is up to date for our purposes."""

    def upgrade_environment(self, db):
        """Make changes to environment to support our needs."""
