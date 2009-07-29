"""
ComponentDependencyPlugin:
a plugin for Trac
http://trac.edgewall.org
"""

from componentdependencies.interface import IRequireComponents
from trac.core import *
from trac.env import IEnvironmentSetupParticipant


class ComponentDependencyPlugin(Component):

    implements(IEnvironmentSetupParticipant)
    dependencies = ExtensionPoint(IRequireComponents)

    ### methods for IEnvironmentSetupParticipant

    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""

    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.
        """
        for dependency in self.dependencies:
            for requirement in dependency.requires():
                if not self.env.is_component_enabled(requirement):
                    return True
        return False
                


    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        needed = set()
        
        for dependency in self.dependencies:
            for requirement in dependency.requires():
                if not self.env.is_component_enabled(requirement):
                    needed.add(requirement)
        needed = set([ '%s.%s' % (i.__module__, i.__name__.lower()) for i in needed ])
        for component in needed:
            self.config.set('components', component, 'enabled')
        self.config.save()
