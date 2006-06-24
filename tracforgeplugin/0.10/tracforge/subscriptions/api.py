from trac.core import *

# Both of these are placeholders for right now
class ISubscribable(Interface):
    """Extension point interface for objects that can be
    subscribed to."""
    
    def dump_object(obj):
        """Senders side of the object transaction."""
        
    def load_object(data):
        """Recievers side of the object transaction."""
    
class ISubscriptionFilter(Interface):
    """Extension point interface for filters that can restrict or
    process objects while they are being pushed.
    
    Not currently implemented."""
