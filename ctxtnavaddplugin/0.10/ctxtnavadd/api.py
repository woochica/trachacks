from trac.core import *

class ICtxtnavAdder(Interface):
    """An extension point interface to adding ctxtnav entries."""
    
    def match_ctxtnav_add(req):
        """Return True if you want to alter this requests ctxtnav bar."""
        
    def get_ctxtnav_adds(req):
        """Return a list of the form (path, text) to be added to the bar."""
