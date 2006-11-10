# Datamover API classes
from trac.core import *
from trac.web.main import _open_environment
from trac.config import OrderedExtensionsOption
from trac.perm import IPermissionRequestor

class IEnvironmentProvider(Interface):
    """An extension point interface for enumerating local environments."""
    
    def get_environments():
        """Enumerate known environments. Should return an iterable of environment paths."""
        
    def add_environment(path):
        """Add this environment to your list."""

    def delete_environment(path):
        """Remove this environment from your list."""

class DatamoverSystem(Component):
    
    env_providers = ExtensionPoint(IEnvironmentProvider)
    
    implements(IPermissionRequestor)

    # Public methods    
    def all_environments(self):
        """Returns a dictionary of the form {env_path: {'name', 'muable', 'providers'}}."""
        envs = {}
        for provider in self.env_providers:
            for env in provider.get_environments():
                mutable = not hasattr(provider, 'mutable') or provider.mutable
                envs[env] = {
                    'name': _open_environment(env).project_name,
                    'mutable': mutable and envs.get(env, {'mutable': True}).get('mutable'),
                    'providers': envs.get(env, {'providers': []}).get('providers') + [provider], # TODO: This could be better written (list.setdefault)
                }

        return envs

    def any_mutable(self):
        """Indicate if any of the active providers are mutable."""
        for provider in self.env_providers:
            if not hasattr(provider, 'mutable') or provider.mutable:
                return True
        return False

    def add_environment(self, path):
        """Add an environment to the first provider that will accept it."""
        for provider in self.env_providers:
            if hasattr(provider, 'mutable') and not provider.mutable:
                continue # Ignore immutable providers
            if provider.add_environment(path):
                return # Accepted, we are done
        raise TracError('Unable to add environment at %s'%path)

    def delete_environment(self, path):
        """Delete an environment from all containing providers."""
        envs = self.all_environments()
        if path not in envs: return # NOTE: Should this be an error?
        if not envs[path]['mutable']:
            # XXX: Wow, thats a pretty confusing error
            raise TracError('Cannot remove environment at %s, it is contributed by an immutable provider'%path) 
        for provider in envs[path]['providers']:
            provider.delete_environment(path)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['DATAMOVER_ADMIN']
