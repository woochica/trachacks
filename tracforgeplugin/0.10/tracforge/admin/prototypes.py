# Utility classes for the TracForge prototypes system
from trac.core import *
from api import IProjectSetupParticipant

import inspect

class ProjectSetupParticipantBase(Component):
    """Base class for project setup participants."""
    # Based on WikiMacroBase
    
    abstract = True
    
    implements(IProjectSetupParticipant)

    def get_setup_actions(self):
        name = self.__class__.__name__
        if name.endswith('Action'):
            name = name[:-6]
        yield name

    def get_setup_action_description(self, action):
        return inspect.getdoc(self.__class__)
        
    def execute_setup_action(self, req, env_path, action, args):
        raise NotImplementedError()

class MakeTracEnvironmentAction(ProjectSetupParticipantBase):
    """Make a new Trac environment using trac-admin initenv."""
    
    def execute_setup_action(self, req, env_path, action, args):
        pass

class MakeSubversionRepositoryAction(ProjectSetupParticipantBase):
    """Make a new Subversion repository using `svnadmin create`."""
    
    def execute_setup_action(self, req, env_path, action, args):
        pass

class ApplyConfigSetAction(ProjectSetupParticipantBase):
    """Apply a ConfigSet to a Trac environment."""
    
    def execute_setup_action(self, req, env_path, action, args):
        pass
