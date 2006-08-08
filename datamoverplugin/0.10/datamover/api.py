# Datamover API classes
from trac.core import *
from trac.env import Environment

class IEnvironmentProvider(Interface):
    """An extension point interface for enumerating local environments."""
    
    def get_environments():
        """Enumerate known environments. Should return an iterable of environment paths."""
        
    def mutable_environments():
        """Is the list provided by this plugin mutable (does it support deletion)."""
        
    def delete_environment(env):
        """Remove this environment from your list."""

class DatamoverSystem(Component):
    
    env_providers = ExtensionPoint(IEnvironmentProvider)
    
    def all_environments(self):
        """Returns a dictionary of the form {env_path: {'name', 'muable', 'providers'}}."""
        envs = {}
        for provider in self.env_providers:
            for env in provider.get_environments():
                envs[env] = {
                    'name': Environment(env).project_name,
                    'mutable': provider.mutable_environments() and envs.get(env, {'mutable': 1}).get('mutable'),
                    'provider': envs.get(env, {'provider': []}).get('provider') + [provider],
                }

        return envs

