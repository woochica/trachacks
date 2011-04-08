from trac.core import *
from trac.env import IEnvironmentSetupParticipant
import trac.ticket.notification as notification


class NotifyAllUSersPlugin(Component):
    """
    This component monkey patches notification.TicketNotifyEmail.get_recipients so that trac sends email to all users
    """
    implements(IEnvironmentSetupParticipant)

    def __init__(self):
        old_get_recipients = notification.TicketNotifyEmail.get_recipients

        cls = self.__class__

        def new_get_recipients(self, tktid):
            if not self.env.is_component_enabled(cls):
                return old_get_recipients(self, tktid)
            else:
                to_recipients = []
                cc_recipients = []
                for _username, _name, email in self.env.get_known_users(self.db):
                    if email is not None:
                        to_recipients.append(email)
                return to_recipients, cc_recipients

        notification.TicketNotifyEmail.get_recipients = new_get_recipients

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        pass

    def upgrade_environment(self, db):
        pass




