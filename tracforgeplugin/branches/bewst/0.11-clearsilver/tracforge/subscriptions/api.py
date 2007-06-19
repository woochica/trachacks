from trac.core import *

# Both of these are placeholders for right now
class ISubscribable(Interface):
    """Extension point interface for objects that can be
    subscribed to."""
    
    def subscribable_types():
        """A list of all object types (as tags) that this module handles."""
        
    # Mostly to remind myself, the reason this interface has no other
    # functions is because during an object transaction, the only thing
    # that it has to interact with is itself (1 instance on either side 
    # of the transaction). Because of this, there is no need for a formal
    # interface specification for how to send or recieve objects, each
    # plugin can use whatever means work for it.
    
class ISubscriptionFilter(Interface):
    """Extension point interface for filters that can restrict or
    process objects while they are being pushed.
    
    Not currently implemented."""
    pass
