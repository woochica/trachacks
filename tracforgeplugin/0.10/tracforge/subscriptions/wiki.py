# TracForge wiki subscription module

from trac.core import *
from trac.wiki.model import WikiPage

from api import ISubscribable

class WikiSubscribable(Component):
    """This class implements wiki subscriptions between environments."""
    
    implements(ISubscribable)
    
    
