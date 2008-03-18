# Utility classes for the TracForge prototypes system
import inspect
import sys
import os
import os.path
import time

from trac.core import *

from tracforge.admin.api import IProjectSetupParticipant
from tracforge.admin.util import CommandLine, locate

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
        
    def execute_setup_action(self, action, args, data, log_cb):
        raise NotImplementedError

    def call_external(self, log_cb, executable, *args):
        path = executable
        if not os.path.isabs(path):
            path = locate(path)
        if path is None:
            log_cb('', 'Unable to locate %s'%executable)
            return False
        cl = CommandLine(path, args)
        for stdout, stderr in cl.execute():
            log_cb(stdout, stderr)
        return cl.returncode == 0


class MakeTracEnvironmentAction(ProjectSetupParticipantBase):
    """DO NOT USE. Make a new Trac environment using trac-admin initenv."""
    #capture_output = False
    def execute_setup_action(self, action, args, data, log_cb):
        from trac.admin.console import run
        
        return run([data['path'], 
                    'initenv', 
                    data['full_name'], 
                    'sqlite:db/trac.db', 
                    data.get('repo_type', ''),
                    data.get('repo_dir', ''),
                   ]) == 0


class MakeSubversionRepositoryAction(ProjectSetupParticipantBase):
    """DO NOT USE. Make a new Subversion repository using `svnadmin create`."""
    capture_output = False
    def execute_setup_action(self, action, args, data, log_cb):
        if '%s' not in args:
            args = os.path.join(args, '%s')
        repo_dir = args%data['name']
        data['repo_type'] = 'svn'
        data['repo_dir'] = repo_dir
        return self.call_external(log_cb, 'svnadmin', 'create', repo_dir)


class ApplyConfigSetAction(ProjectSetupParticipantBase):
    """DO NOT USE. Apply a ConfigSet to a Trac environment."""
    
    def execute_setup_action(self, action, args, data, log_cb):
        print 'Output 1'
        print 'Output 2\nOutput 3'
        print >>sys.stderr,'Error 1'
        print 'Output 4'
        #os.system('echo "Output 5"')
        return True


class DoNothingAction(ProjectSetupParticipantBase):
    """Do nothing, just like it says.."""
    
    def execute_setup_action(self, action, args, data, log_cb):
        return True
