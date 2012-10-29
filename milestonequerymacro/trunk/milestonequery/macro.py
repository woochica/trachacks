# -*- coding: utf-8 -*-

from genshi.core import Markup
from trac.wiki.formatter import Formatter
from trac.wiki.macros import WikiMacroBase, parse_args
from StringIO import StringIO

class MilestoneQueryMacro(WikiMacroBase):
    """Display a ticket query based on the milestone name for each matching milestone.

    Specify a pattern to match the milestones and optionally
    'completed' and 'desc' (or 'asc' which is the default):

      [[MilestoneQuery(rc_%)]]

      [[MilestoneQuery(release_%, completed)]]

      [[MilestoneQuery(release_%, completed, DESC)]]

    The pattern is a SQL LIKE pattern.
    """

    def expand_macro(self, formatter, name, content):
        args, kwargs = parse_args(content)
        pattern = args[0]
        if len(args) > 1 and args[1].strip().upper() == "COMPLETED":
            completed = "AND completed>0"
        else:
            completed = "AND completed=0"
        if len(args) > 2 and args[2].strip().upper() == "ASC":
            ordering = "ASC"
        else:
            ordering = "DESC"

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        print """
            SELECT name FROM milestone WHERE name %s
              %s ORDER BY name %s
            """ % (db.like(), completed, ordering)
        cursor.execute("""
            SELECT name FROM milestone WHERE name %s
              %s ORDER BY name %s
            """ % (db.like(), completed, ordering), (pattern,)
        )

        out = StringIO()
        for name, in cursor.fetchall():
            wikitext = """
                == [milestone:%(milestonename)s %(milestonename)s] ==
                [[TicketQuery(milestone=%(milestonename)s,order=id,desc=0,format=table,col=summary|owner|ticket_status|type|status)]]
                """ % {'milestonename': name}
            Formatter(self.env, formatter.context).format(wikitext, out)

        return Markup(out.getvalue())


