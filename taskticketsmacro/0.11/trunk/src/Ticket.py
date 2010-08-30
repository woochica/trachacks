"""Inserts the current time (in seconds) into the wiki page."""

from genshi.builder import tag
from StringIO import StringIO
from trac.util.html import escape,html,plaintext
from trac.wiki.macros import WikiMacroBase
from genshi.core import Markup
from trac.wiki.formatter import Formatter

revison = "$Rev$"
url = "$URL$"

class TicketMacro(WikiMacroBase):

    def expand_macro(self, formatter, name, args):
        env = formatter.env
        req = formatter.req

        arg = args.split('||')
        duedate = arg[0].strip()
        summary = arg[1].strip()
        effort = arg[2].strip()
        user = req.args['user']
        project = req.args['project']

        db = env.get_db_cnx()
        cursor = db.cursor()

        sql = "SELECT id, owner, summary, description, status FROM ticket WHERE summary=%s"
        cursor.execute(sql, [summary]) 

        row = cursor.fetchone()
        if row==None:     
            link = html.A(escape(summary), href="%s?field_summary=%s&field_type=task&field_duedate=%s&field_effort=%s&field_owner=%s&field_project=%s" %   
                                                    (env.href.newticket(),
                                                    escape(summary),
                                                    escape(duedate),
                                                    escape(effort),
                                                    escape(user),
                                                    escape(project)))
        else:
            user = row[1]
            link = html.A("#%s %s" % (row[0],escape(row[2])), href=env.href.ticket(row[0]), class_=row[4])

        req.args['effort'] = req.args['effort'] + float(effort)

        return html.TR(
            html.TD(escape(user)),
            html.TD(duedate),
            html.TD(link),
            html.TD(effort)
        )         

        # text = StringIO();
        
        # text.write('<tr><td>'+escape(user)+'</td><td>'+duedate+'</td><td>'+buf+'</td><td>'+effort+'</td></tr>')
        # text.write(buf)
        # return text.getvalue()
