# -*- coding: utf-8 -*-

from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.env import IEnvironmentSetupParticipant
from trac.util.translation import domain_functions


_, N_, tag_, tagn_, gettext, ngettext, tgettext, tngettext, add_domain = \
    domain_functions(
        'tracexceldownload',
        '_', 'N_', 'tag_', 'tagn_', 'gettext', 'ngettext', 'tgettext',
        'tngettext', 'add_domain')


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
