# Datamover API classes
from trac.core import *
from trac.web.main import _open_environment

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
                    'name': _open_environment(env).project_name,
                    'mutable': provider.mutable_environments() and envs.get(env, {'mutable': True}).get('mutable'),
                    'provider': envs.get(env, {'provider': []}).get('provider') + [provider],
                }

        return envs

    def any_mutable(self):
        """Indicate if any of the active providers are mutable."""
        for provider in self.env_providers:
            if provider.mutable_environments():
                return True
        return False
