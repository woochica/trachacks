from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import format_to_html

from randomwiki import *

__all__ = ['RandomQuoteMacro']

class RandomQuoteMacro(Component):
    """
    Displays a (pseudo-)randomly chosen quote from a source page.  If no
    source page is supplied, the page "Fortune Cookies" is used.  Each quote
    on the source page should be a bulleted item (i.e., preceded by *).
    {{{

    [[RandomQuote]]

    [[RandomQuote(QuotePage)]]

    }}}

    """

    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'RandomQuote'

    def get_macro_description(self, name):
        return inspect.getdoc(RandomQuoteMacro)


    def expand_macro(self, formatter, name, txt):

        if txt:
            sourcepage = txt.strip('"')
        else:
            sourcepage = 'Fortune Cookies'

        wikiobj = randomwiki(self.env.get_db_cnx())
        pagelist = wikiobj.getentries(sourcepage,1)
        if pagelist[0]:
            pagelist[0] = pagelist[0].replace('*','')
            return format_to_html(self.env,formatter.context,pagelist[0])
        else:
            return "Quotes not found"
        
