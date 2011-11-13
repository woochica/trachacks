# -*- coding: utf-8 -*-

from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.env import IEnvironmentSetupParticipant
try:
    from trac.util.translation import domain_functions
except ImportError:
    domain_functions = None


if domain_functions:
    from trac.util.translation import dgettext, dngettext

    _, N_, gettext, add_domain = domain_functions(
        'tracexceldownload', '_', 'N_', 'gettext', 'add_domain')

    class TranslationModule(Component):

        implements(IEnvironmentSetupParticipant)

        def __init__(self, *args, **kwargs):
            Component.__init__(self, *args, **kwargs)
            add_domain(self.env.path, resource_filename(__name__, 'locale'))

        # IEnvironmentSetupParticipant methods
        def environment_created(self):
            pass

        def environment_needs_upgrade(self, db):
            return False

        def upgrade_environment(self, db):
            pass

else:
    from trac.util.translation import _, N_, gettext

    def dgettext(domain, string, **kwargs):
        if kwargs:
            return string % kwargs
        return string

    def dngettext(domain, singular, plural, num, **kwargs):
        kwargs = kwargs.copy()
        kwargs.setdefault('num', num)
        if num != 1:
            string = plural
        else:
            string = singular
        return string % kwargs
