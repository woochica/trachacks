# Changeset sync module

# As changesets aren't objects, all this does is provide

from trac.core import *
from trac.Timeline import ITimelineEventProvider
from trac.versioncontrol.web_ui.changeset import ChangesetModule

from api import ISubscribable

class ChangesetSubscribable(Component):
    """Provide remote changeset events to the local timeline."""
    
    implements(ISubscribable)
    
    def subscribable_types(self):
        yield 'changeset'
