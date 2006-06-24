from trac.core import *
from trac.config import *
from trac.config import OrderedExtensionsOption

from tracforge.api import *
from tracforge.util import *
from tracforge.config import *

import os

class SubscriptionManagerModule(Component):
    """A class that manages data subscriptions."""

    subscribers = ListDictOption('tracforge-subscribers', sep=os.pathsep, 
                               doc="""A list of env paths that want to recieve updates from this project.""")
    subscribtion_filters = OrderedExtensionsOption('tracforge-client','filters',ISubscriptionFilter,
                               include_missing=False, doc="""Filters for recieved data.""")

    subscribables = ExtensionPoint(ISubscribable)
    
    def __init__(self):
        pass
        
    def subscibe_to(self, source, type):
        source_env = open_env(sorce)
        source_mgr = SubscriptionManagerModule(source_env)
        source_mgr._add_subscription(self.env, type)
        
    def _add_subscription(self, dest, type):
        dest_env = open_env(dest)
        dest_path = dest_env.path
        self.config.set('tracforge-subscribers',type,os.pathsep.join(self.subscribers+dest_path))
        self.config.save()
