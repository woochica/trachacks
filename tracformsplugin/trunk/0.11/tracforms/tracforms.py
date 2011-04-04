# -*- coding: utf-8 -*-

from pkg_resources  import resource_filename

from trac.core import Component

# Import i18n methods.  Fallback modules maintain compatibility to Trac 0.11
# by keeping Babel optional here.
try:
    from trac.util.translation import domain_functions
    add_domain, _, ngettext = \
        domain_functions('tracforms', ('add_domain', '_', 'ngettext'))
except ImportError:
    from trac.util.translation import gettext
    _ = gettext
    ngettext = _
    def add_domain(a,b,c=None):
        pass


class TracFormPlugin(Component):
    """Provides i18n support for TracForms."""

    def __init__(self):
        # bind the 'tracforms' catalog to the specified locale directory
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

