# Utility classes for the TracForge prototypes system
from trac.core import *
from api import IProjectSetupParticipant

import inspect
import sys
import os
import time

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
        
    def execute_setup_action(self, req, proj, action, args):
        raise NotImplementedError

class MakeTracEnvironmentAction(ProjectSetupParticipantBase):
    """DO NOT USE. Make a new Trac environment using trac-admin initenv."""
    
    def execute_setup_action(self, req, proj, action, args):
        repo_type = hasattr(proj, 'repo_type') and proj.repo_type or 'svn'
        repo_path = hasattr(proj, 'repo_path') and proj.repo_path or ''
    
        from trac.config import default_dir
        from trac.scripts.admin import run
        return run([proj.env_path, 
                    'initenv', 
                    req.args.get('fullname','').strip(), 
                    'sqlite:db/trac.db', 
                    repo_type.strip(), 
                    repo_path.strip(), 
                    default_dir('templates'),
                   ]) == 0

class MakeSubversionRepositoryAction(ProjectSetupParticipantBase):
    """DO NOT USE. Make a new Subversion repository using `svnadmin create`."""
    
    def execute_setup_action(self, req, proj, action, args):
        print 'Failed output'
        print >>sys.stderr, 'Failed error 1\nFailed error 2\nFailed error 3'
        time.sleep(60)
        return False

class ApplyConfigSetAction(ProjectSetupParticipantBase):
    """DO NOT USE. Apply a ConfigSet to a Trac environment."""
    
    def execute_setup_action(self, req, proj, action, args):
        print 'Output 1'
        print 'Output 2\nOutput 3'
        print >>sys.stderr,'Error 1'
        print 'Output 4'
        os.system('echo "Output 5"')
        return True

class DoNothingAction(ProjectSetupParticipantBase):
    """Do nothing, just like it says.."""
    
    def execute_setup_action(self, req, proj, action, args):
        return True
