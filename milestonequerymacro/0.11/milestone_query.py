from genshi.core import Markup
from trac.wiki.macros import WikiMacroBase
from trac.wiki import Formatter
from StringIO import StringIO

class MilestoneQueryMacro(WikiMacroBase):
    """Display a ticket query based on the milestone name for each matching milestone.

    Specify a pattern to match the milestones and optionally
    'completed' and 'desc' (or 'asc' which is the default):

      [[MilestoneQuery(rc_%,,)]]

      [[MilestoneQuery(release_%, completed,)]]

      [[MilestoneQuery(release_%, completed, DESC)]]

    The pattern is a SQL LIKE pattern.
    """

    #revision = "0.1"
    #url = "http://making.dev.woome.com"

    def expand_macro(self, formatter, name, text):
        pattern, completed, order = text.split(",")
        cursor = self.env.get_db_cnx().cursor()
        cursor.execute(
            "SELECT name FROM milestone WHERE name like '%s' %s %s;" % (
                pattern,
                "AND completed > 0" if completed else "",
                "ORDER BY name ASC" \
                    if (order.upper() == "ASC" or order == "") \
                    else "ORDER BY name DESC"
                )
            )
        milestone_names = [mn[0] for mn in cursor]

        out = StringIO()
        for m in milestone_names:
            wikitext = """== %(milestonename)s ==\n[[TicketQuery(milestone=%(milestonename)s,order=id,desc=0,format=table,col=summary|owner|ticket_status|type|status)]]""" % {
                "milestonename": m
                }
            Formatter(self.env, formatter.context).format(wikitext, out)

        return Markup(out.getvalue())

# End
