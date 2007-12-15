from trac.core import *
from trac.wiki.api import IWikiMacroProvider, WikiSystem
from trac.wiki.formatter import format_to_html
from trac.wiki.model import WikiPage
import re

from randomwiki import *

__all__ = ['RandomItemMacro']

class RandomItemMacro(Component):
    """
    Displays a (pseudo-)randomly chosen list of bulleted items from
    the supplied source page.  For example:
    {{{

    [[RandomItem("RandomPages",10)]]

    }}}

    will find 10 bulleted (*) items on RandomPages and include those items
    in the current page.
    """

    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'RandomItem'

    def get_macro_description(self, name):
        return inspect.getdoc(RandomItemMacro)

    def fixup_images(self,page,pagename):
        '''
        prepend the current page name to the image name so it renders
        correctly in the target page
        '''
        r = re.compile(r'\[\[Image\((.+?)\)\]\]')
        m = r.search(page)
        if m:
            page = page.replace('*','')
            page = page.replace(m.group(0),
                                '[[Image(wiki:'+pagename+':'+m.group(1)+')]]')
        return page

    def expand_macro(self, formatter, name, txt):

        (sourcepage,number) = txt.split(',')
        sourcepage = sourcepage.strip('"')
        if number is None:
            number = 1
        else:
            number = int(number)

        out = ''
        wikiobj = randomwiki(self.env.get_db_cnx())
        pagelist = wikiobj.getentries(sourcepage,number)
        for page in pagelist:
            page = self.fixup_images(page,sourcepage)
            out += format_to_html(self.env,formatter.context,page)

        return out
        
