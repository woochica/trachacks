from genshi.core import Markup
from trac.wiki.macros import WikiMacroBase
from trac.wiki import Formatter
from StringIO import StringIO

class WikiQueryMacro(WikiMacroBase):
    """Display the text of a specified text of number of wiki pages based on a match query.

    The default number of pages to display is 10.

      [[WikiQuery(NicFerrier/blog/%,)]]

      [[WikiQuery(%/blog/%, 25)]]

    The pattern is a SQL LIKE pattern.
    """

    #revision = "0.1"
    #url = "http://making.dev.woome.com"

    def expand_macro(self, formatter, name, text):
        pattern, limit = text.split(",")
        if limit == "":
            limit = 10
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute(
            """SELECT comment,text 
FROM wiki w
WHERE version = (SELECT max(version) FROM wiki WHERE name = w.name)
AND name like '%(pattern)s' ORDER BY time DESC LIMIT %(limit)s;""" % {
                "pattern": pattern,
                "limit": limit
                }
            )
        pages = [(p[0],p[1]) for p in cursor]
        out = StringIO()
        for comment, text in pages:
            wikitext = """== %(comment)s ==\n%(text)s""" % {
                "comment": comment,
                "text": text
                }
            Formatter(self.env, formatter.context).format(wikitext, out)

        return Markup(out.getvalue())

# End
