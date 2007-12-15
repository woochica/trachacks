from trac.core import *
from trac.wiki.api import IWikiMacroProvider, WikiSystem

__all__ = ['UserCountMacro']

class UserCountMacro(Component):
    """A macro to a count of registered users
    {{{
    [[UserCount]]
    }}}
    Note:  This macro works only if your installation stores usernames
    in the database.
    """

    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'UserCount'

    def expand_macro(self, formatter, name, txt):

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute('''SELECT count(*)
                              FROM session_attribute
                              WHERE name = "name" ''')
        except:
            return '0'

        row = cursor.fetchone()
        return row[0]
        
