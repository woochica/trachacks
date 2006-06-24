# TracForge model abstractions

from util import *

class Forge(object):
    """A class representing an entire 
    forge (a group of linked projects)."""
    
    master_env_path = Option('tracforge','master_env',
                        doc="Name or path to the forge controller")
    
    def __init__(self, env):
        """In this case, env should always be 
        the environment of the current Trac."""
        self.env = env
        self.master_env = open_env(self.master_env_path)

    config = property(lambda self: self.env.config) # Needed for trac.config descriptors


class Project(object):
    """A class representing a single project in a forge."""

    
    
    def __init__(self, env):
        """The env should be the env name for the desired project."""
        self.env = open_env(env)

    config = property(lambda self: self.env.config) # Needed for trac.config descriptors
        
    def subscribers(self, type):
        """
