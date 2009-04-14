"""
CustomFieldProvider:
a plugin for Trac to provide custom ticket fields programmatically
http://trac.edgewall.org/wiki/TracTicketsCustomFields
"""

from interface import ICustomFieldProvider

from trac.core import *
from trac.env import IEnvironmentSetupParticipant

class CustomFieldProvider(Component):

    implements(IEnvironmentSetupParticipant)
    customfields = ExtensionPoint(ICustomFieldProvider)

    ### methods for IEnvironmentSetupParticipant

    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""

    def environment_created(self):
        """Called when a new Trac environment is created."""
        self.upgrade_environment(None)

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.
        """

        self.upgrade_environment(None)
        return False

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """

        # TODO: check for overlapping fields

        for provider in self.customfields:
            for field, options in provider.fields().items():
                
                if options is None:
                    options = {}

                # ensure the name is kosher
                for i in '. \t\n\r':
                    assert i not in field

                # set field type
                fieldtype = options.setdefault('type', 'text')
                self.config.set('ticket-custom', field, fieldtype)
                options.pop('type')
                
                # process options
                if 'label' not in options:
                    options['label'] = field.title()
                if 'options' in options:
                    options['options'] = '|'.join(options['options'])

                # set the options
                for option, value in options.items():
                    self.config.set('ticket-custom', '%s.%s' % (field, option), value)

        # save the configuration
        self.config.save()
