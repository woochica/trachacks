from trac.core import *

from tracforge.util import *

class SubscriptionManagerModule(Component):
    """A class that manages data subscriptions."""

    subscribtion_filters = OrderedExtensionOption('tracforge-client','filters',
                               include_missing=False, doc="""Filters for recieved data.""")

    subscribables = extension_point(ISubscribable)
    
    def __init__(self):
        pass
        
    def subscibe_to(self, source, type):
        source_env = open_env(sorce)
        source_mgr = SubscriptionManagerModule(source_env)
        source_mgr._add_subscription(self.env, type)
        
    def _add_subscription(self, dest, type):
        dest_env = open_env(dest)
        dest_path = dest_env.path
        subscribers = self.config.get('tracforge-client',type,default='')
        subscribers = os.pathsep.split(subscribers)
        subscribers.append(dest)
        self.config.set('tracforge-client',type,os.pathsep.join(subscribers))
        self.config.save()
