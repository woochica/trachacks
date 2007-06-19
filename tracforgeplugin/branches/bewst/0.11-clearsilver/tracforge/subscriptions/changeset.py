# Changeset sync module

# As changesets aren't objects, all this does is provide

from trac.core import *
from trac.timeline import ITimelineEventProvider
from trac.versioncontrol.web_ui.changeset import ChangesetModule
from trac.web.href import Href
from trac.util import Markup

from api import ISubscribable
from util import open_env
from manager import SubscriptionManager
from config import DictOption

import traceback, sys, os

class PseudoRequest(object):
    """A wrapper to redirect req.href elsewhere."""
    # TODO: Alter req.abs_href too
    
    def __init__(self, req, href):
        self.req = req
        self.href = href
        
    def __getattr__(self, name):
        return getattr(self.req, name)

class ChangesetSubscribable(Component):
    """Provide remote changeset events to the local timeline."""
    
    env_map = DictOption('tracforge-envs', doc="Map of the form '/path/to/env = /url/base'")
    
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
                
                # Try to isolate the base URL to the other Trac
                base = ''
                if env in self.env_map: # First use our own mapping
                    base = self.env_map[base]
                else:
                    env_basename = os.path.split(env.path.rstrip(os.sep))[1]
                    if self.config.get('intertrac', env_basename+'.url'): # Then try using an intertrac link
                        base = self.config.get('intertrac', env_basename+'.url')
                    else: # And finally look for a sibling path
                        self.log.debug('ChangesetSubscribable: Falling back to sibling computation, base is %s'%env_basename)
                        url = req.href().rstrip('/').split('/')
                        url.pop()
                        url.append(env_basename)
                        base = '/'.join(url)

                self.log.debug('ChangesetSubscribable: Computed base URL of %s to be %s'%(env.path, base))
                new_href = Href(base)
                env.href = new_href
                new_req = PseudoRequest(req, new_href)
                cset = ChangesetModule(env)
                try:
                    for ret in cset.get_timeline_events(new_req, start, stop, ['changeset']):
                        kind, href, title, date, author, message = ret
                        title += Markup(' from %s',env.config.get('project','name',env.path))
                        yield (kind, href, title, date, author, message)
                except Exception, e:
                    self.log.debug('ChangesetSubscribable: %s'%traceback.format_exc())
                    raise e
