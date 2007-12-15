from trac.core import *
from trac.wiki.api import IWikiMacroProvider, WikiSystem

__all__ = ['AnchorMacro']

class PageCountMacro(Component):
    """Creates an html anchor element for the given anchor name.
    {{{
    [[Anchor(anchorname)]]
    }}}
    """

    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'Anchor'

    def expand_macro(self, formatter, name, txt):
        txt = txt.replace('"','')
        return "<a name=\"txt\"/>"
