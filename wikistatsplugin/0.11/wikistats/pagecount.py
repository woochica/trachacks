from trac.core import *
from trac.wiki.api import IWikiMacroProvider, WikiSystem

__all__ = ['PageCountMacro']

class PageCountMacro(Component):
    """Counts the number of pages in the wiki
    {{{
    [[PageCount]]
    }}}
    """

    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'PageCount'

    def expand_macro(self, formatter, name, txt):

        # note that the wiki api caches the number of pages but has
        # no method to count them.  if performance is an issue, mod
        # the api
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute('''SELECT COUNT(DISTINCT(name)) FROM wiki ''')
        except:
            return '0'

        row = cursor.fetchone()
        return str(row[0])
        
