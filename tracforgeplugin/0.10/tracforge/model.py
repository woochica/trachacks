# TracForge model abstractions

from tracforge.util import *

class Forge(object):
    """A class representing an entire 
    forge (a group of linked projects."""
    
    master_env_path = Option('tracforge','master_env',
                        doc="Name or path to the forge controller")
    
    def __init__(self, env):
        """In this case, env should always be 
        the environment of the current Trac."""
        self.env = env
        self.config = env.config # Needed for trac.config descriptors
        self.master_env = open_env(self.master_env_path)
