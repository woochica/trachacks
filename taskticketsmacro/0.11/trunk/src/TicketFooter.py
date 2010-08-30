"""Inserts the current time (in seconds) into the wiki page."""

from genshi.builder import tag
from StringIO import StringIO
from trac.util.html import escape
from trac.wiki.macros import WikiMacroBase

revison = "$Rev$"
url = "$URL$"

class TicketFooterMacro(WikiMacroBase):

    def expand_macro(self, formatter, name, args):
        req = formatter.req
        out = StringIO()
        out.write("<tr><td></td><td></td><td></td><td><b>%s</b><td></tr>"%(req.args['effort']))
        out.write(" </table>")
        return out.getvalue()
