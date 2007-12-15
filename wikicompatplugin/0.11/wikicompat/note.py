from trac.core import *
from trac.wiki.api import IWikiMacroProvider, WikiSystem

__all__ = ['NoteMacro']

class NoteMacro(Component):
    """Creates a non-printing note to transmit comments about the
    entry to other wiki authors.  This is especially useful in templates.
    {{{
    [[Note(Be sure to replace the following with a real phone number) ]]
    }}}
    """

    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'Note'

    def expand_macro(self, formatter, name, txt):
        return ''
        
