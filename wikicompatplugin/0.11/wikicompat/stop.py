from trac.core import *
from trac.wiki.api import IWikiMacroProvider, WikiSystem
from trac.wiki.model import WikiPage

__all__ = ['StopMacro']

class StopMacro(Component):
    """Creates a box directing readers to the talk page.
    {{{
    [[Stop]]
    }}}
    """

    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'Stop'

    def expand_macro(self, formatter, name, txt):
        resource = formatter.resource
        page = WikiPage(self.env,resource)
        name = page.name
        return '''<center>
                  <table style=\"border: 1px solid #CBCBCB;width: 400px; font-size: x-small;"><tr><td style="padding: 2px;">%s</td>
                  <td style="padding: 2px;">In an effort to promote a more open dialogue, discussion about the content of this page should continue at <a href="%s/Talk">%s/Talk</a></td>
                  </tr></table></center>''' % ('[STOP]',name,name)
        
