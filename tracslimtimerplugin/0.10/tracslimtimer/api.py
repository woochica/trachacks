
from trac.core import *
from trac.env import IEnvironmentSetupParticipant

class TracSlimTimerSetupParticipant(Component):
    """
    We need:
    [ticket-custom]

    slimtimer_id = text
    slimtimer_id.value = 0
    slimtimer_id.label = SlimTimer ID
    slimtimer_id.order = 99
    """
    implements(IEnvironmentSetupParticipant)

    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be
        upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.

        """
        ticket_custom = "ticket-custom"
        return not (self.config.get( ticket_custom, "slimtimer_id" ) == "text")
            
    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        print "Upgrading TracSlimTimer custom fields"

        ticket_custom = "ticket-custom"

        self.config.set(ticket_custom, "slimtimer_id", "text")
        self.config.set(ticket_custom, "slimtimer_id.value", "0")
        self.config.set(ticket_custom, "slimtimer_id.label", "SlimTimer ID")
        self.config.set(ticket_custom, "slimtimer_id.order", "99")
        self.config.save();

        print "Done upgrading TracSlimTimer custom fields"

