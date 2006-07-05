# Changeset sync module

# As changesets aren't objects, all this does is provide

from trac.core import *
from trac.Timeline import ITimelineEventProvider
from trac.versioncontrol.web_ui.changeset import ChangesetModule

from api import ISubscribable
from util import open_env
from manager import SubscriptionManager

import traceback, sys

class ChangesetSubscribable(Component):
    """Provide remote changeset events to the local timeline."""
    
    implements(ISubscribable, ITimelineEventProvider)
    
    # ISubscribable methods
    def subscribable_types(self):
        yield 'changeset'

    # ITimelineEventProvider methods
    def get_timeline_filters(self, req):
        yield ('remote_changeset', 'External repository checkins')

    def get_timeline_events(self, req, start, stop, filters):
        if 'remote_changeset' in filters:
            for source in SubscriptionManager(self.env).get_subscriptions('changeset'):
                env = open_env(source)
                cset = ChangesetModule(env)
                try:
                    for ret in cset.get_timeline_events(req, start, stop, ['changeset']):
                        yield ret
                except Exception, e:
                    self.log.debug('ChangesetSubscribable: %s'%traceback.format_exc())
                    raise e
