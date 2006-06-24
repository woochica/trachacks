from trac.core import *
from trac.config import *
from trac.config import OrderedExtensionsOption

from api import *
from util import *
from config import *

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
        source_mgr._change_subscription('add', self.env, type)
        
    def unsubscribe_from(self, source, type):
        source_env = open_env(sorce)
        source_mgr = SubscriptionManagerModule(source_env)
        source_mgr._change_subscription('delete', self.env, type)

    def _change_subscription(self, action, dest, type):
        dest_env = open_env(dest)
        dest_path = dest_env.path
        if action == 'add':
            self.config.set('tracforge-subscribers',type,os.pathsep.join(self.subscribers[type]+dest_path))
        elif action == 'delete':
            paths = self.subscriptions[type]
            if dest_path in paths:
                paths.remove(dest_path)
                self.config.set('tracforge-subscribers',type,os.pathsep.join(paths))
        else:
            raise TracError, 'Unknown subscription operation'
        self.config.save()

