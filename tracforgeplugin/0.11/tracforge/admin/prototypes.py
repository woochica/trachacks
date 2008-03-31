# Utility classes for the TracForge prototypes system
import inspect
import sys
import os
import os.path
import time

from trac.core import *
from trac.util.compat import reversed
from pkg_resources import resource_stream

from tracforge.admin.api import IProjectSetupParticipant
from tracforge.admin.util import CommandLine, locate

# Try and use ctypes to get fchmod
try:
    import ctypes
    import ctypes.util
    have_ctypes = True
    
    libc = ctypes.CDLL(ctypes.util.find_library('c'))
except ImportError:
    have_ctypes = False

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
    
    def get_setup_action_info(self, action):
        info = {}
        
        doc = inspect.getdoc(self.__class__)
        if doc:
            info['description'] = doc
        if hasattr(self.__class__, 'depends'):
            info['depends'] = self.__class__.depends
        if hasattr(self.__class__, 'optional_depends'):
            info['optional_depends'] = self.__class__.optional_depends
        if hasattr(self.__class__, 'provides'):
            info['provides'] = self.__class__.provides
        return info
    
    def get_setup_action_default(self, action, env):
        return None
    
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
    """Make a new Trac environment using trac-admin initenv."""
    
    optional_depends = ['repo_type', 'repo_dir']
    
    provides = ['env']
    
    def get_setup_action_default(self, action, env):
        return os.path.dirname(env.path)
    
    def execute_setup_action(self, action, args, data, log_cb):
        from trac.admin.console import run
        from trac.env import open_environment
        
        if '%s' not in args:
            args = os.path.join(args, '%s')
        path = args%data['name']
        
        rv = run([path,
                  'initenv',
                  data['full_name'],
                  'sqlite:db/trac.db',
                  data.get('repo_type', ''),
                  data.get('repo_dir', ''),
                 ])
        data['env'] = open_environment(path, use_cache=True)
        return rv == 0


class MakeSubversionRepositoryAction(ProjectSetupParticipantBase):
    """Make a new Subversion repository using `svnadmin create`."""
    
    capture_output = False
    
    provides = ['repo_type', 'repo_dir']
    
    def get_setup_action_default(self, action, env):
        if env.config.get('trac', 'repository_type') == 'svn':
            repo_dir = env.config.get('trac', 'repository_dir')
            if repo_dir:
                return os.path.dirname(repo_dir)
    
    def execute_setup_action(self, action, args, data, log_cb):
        if '%s' not in args:
            args = os.path.join(args, '%s')
        repo_dir = args%data['name']
        data['repo_type'] = 'svn'
        data['repo_dir'] = repo_dir
        return self.call_external(log_cb, 'svnadmin', 'create', repo_dir)


class ApplyConfigSetAction(ProjectSetupParticipantBase):
    """DO NOT USE. Apply a ConfigSet to a Trac environment."""
    
    depends = ['env']
    
    def execute_setup_action(self, action, args, data, log_cb):
        print 'Output 1'
        print 'Output 2\nOutput 3'
        print >>sys.stderr,'Error 1'
        print 'Output 4'
        #os.system('echo "Output 5"')
        return True


class DoNothingAction(ProjectSetupParticipantBase):
    """Do nothing, just like it says.."""
    
    provides = ['foo']
    
    depends = ['foo']
    
    def execute_setup_action(self, action, args, data, log_cb):
        return True


class SetupSubversionHooks(ProjectSetupParticipantBase):
    """Activate the pre and/or post-commit hooks for Subversion.
    
    Valid arguments are `pre`, `post`, or `both`.
    
    '''NOTE''': You cannot automatically activate the pre-commit hook on 
    Windows at this time.
    """
    
    depends = ['repo_type', 'repo_dir']
    
    arg_map = {
        (True, True): 'both',
        (True, False): 'pre',
        (False, True): 'post',
    }
    
    def get_setup_action_defaults(self, action, env):
        if env.config.get('trac', 'repository_type') == 'svn':
            repo_dir = env.config.get('trac', 'repository_dir')
            if repo_dir:
                pre = self._check_hook(repo_dir, 'pre-commit')
                post = self._check_hook(repo_dir, 'post-commit')
                return self.arg_map.get((pre, post))
    
    def execute_setup_action(self, action, args, data, log_cb):
        if data['repo_type'] == 'svn':
            pre, post = dict(reversed(self.arg_map.itertitems())).get(args, (False, False))
            if pre
    
    # Internal methods
    def _check_hook(self, path, hook):
        hook_file = os.path.join(path, 'hooks', hook)
        if os.name == 'nt':
            hook_file += '.bat'
        if not os.path.exists(hook_file):
            return False
        for line in open(hook_file):
            line = line.strip()
            if os.name == 'nt':
                if line.startswith('REM') or line.startswith('::'):
                    continue
            else:
                line = line.split('#', 1)[0]
            if 'trac-'+hook+'-hook' in line:
                return True
        return False
    
    def _install_hook(self, path, hook):
        # Open source and sink for the trac hook
        script = resource_stream(__name__, 'scripts/trac-'+hook+'-hook')
        trachook_file = os.path.join(path, 'hooks', 'trac-'+hook+'-hook') 
        out = open(trachook_file, 'w')
        # Copy over the given trac hook
        data = script.read(1024)
        while data:
            out.write(data)
            data = script.read(1024)
        script.close()
        out.close()
        
        # Add the trac hook to the main hook
        # creating it if needed
        hook_file = os.path.join(path, 'hooks', hook)
        if os.name == 'nt':
            hook_file += '.bat'
        hookf = open(hook_file, 'a')
        hookf.write('%s %s -')  