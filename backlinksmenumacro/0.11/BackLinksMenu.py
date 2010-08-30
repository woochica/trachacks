#
# BackLinksMenu plugin for Trac 1.0
#
# Author: Trapanator trap@trapanator.com
# Website: http://www.trapanator.com/blog/archives/category/trac
#
#
from StringIO import StringIO
from genshi.builder import tag
from trac.wiki.macros import WikiMacroBase
import string
from trac.core import *
from trac.wiki.formatter import format_to_html
from trac.util import TracError
from trac.util.text import to_unicode
from trac.wiki.model import WikiPage

revison = "$Rev$"
url = "$URL$"

class BackLinksMenuMacro(WikiMacroBase):
    """Backlinks

    Note that the name of the class is meaningful:
     - it must end with "Macro"
     - what comes before "Macro" ends up being the macro name

    The documentation of the class (i.e. what you're reading)
    will become the documentation of the macro, as shown by
    the !MacroList macro (usually used in the WikiMacros page).
    """

    revision = "$Rev$"
    url = "$URL$"

    def expand_macro(self, formatter, name, args):
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        thispage = None
        context = formatter.context
        resource = context.resource

        if args:
            thispage = args.replace('\'', '\'\'')
        else:
            #thispage = self.hdf.getValue('wiki.page_name', '')
            thispage = WikiPage(self.env, resource).name

        sql = 'SELECT w1.name FROM wiki w1, ' + \
              '(SELECT name, MAX(version) AS VERSION FROM WIKI GROUP BY NAME) w2 ' + \
              'WHERE w1.version = w2.version AND w1.name = w2.name '

        if thispage:
              #sql += 'AND (w1.text LIKE \'%%[wiki:%s %%\' ' % (to_unicode(thispage, "utf-8").encode ("utf-8"))
              sql += 'AND (w1.text LIKE \'%%[wiki:%s %%\' ' % thispage
              sql += 'OR w1.text LIKE \'%%[wiki:%s]%%\')' % thispage
              #sql += 'OR w1.text LIKE \'%%[wiki:%s]%%\')' % (to_unicode (thispage, "utf-8").encode ("utf-8"))

        cursor.execute(sql)

        buf = StringIO()
        buf.write('<div class="wiki-toc">')
        buf.write('Pages linking to %s:<br />\n' % thispage )

        while 1:
            row = cursor.fetchone()
            if row == None:
                break
            #s2 = unicode (thispage, "utf-8")
            s2 = thispage
            if row[0] == s2:
                pass
            else:
                buf.write('<a href="%s">' % self.env.href.wiki(row[0]))
                buf.write(row[0])
                buf.write('</a><br />\n')

        buf.write('</div>')
        return buf.getvalue()
