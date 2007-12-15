from trac.core import *
from trac.wiki.api import IWikiMacroProvider, WikiSystem

__all__ = ['nbspMacro']

class Nbspmacro(Component):
    """Creates the html element &amp;nbsp; a non-breaking space
    {{{
    [[Nbsp]]
    }}}
    """

    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'Nbsp'

    def expand_macro(self, formatter, name, txt):
        return '&nbsp;'
        
