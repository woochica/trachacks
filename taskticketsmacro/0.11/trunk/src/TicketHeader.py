"""Inserts the current time (in seconds) into the wiki page."""

from genshi.builder import tag
from genshi.core import Markup
from StringIO import StringIO
from trac.util.html import escape,html
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import Formatter

revison = "$Rev$"
url = "$URL$"

class TicketHeaderMacro(WikiMacroBase):

    def expand_macro(self, formatter, name, args):
        req = formatter.req
        arg = args.split('||')
        req.args['user'] = arg[0].strip()
        req.args['project'] = arg[1].strip()
        req.args['effort'] = 0
       
        out = StringIO()
        out.write(" <table class='wiki'>")
        out.write("<tr><td><b>Entwickler</b></td><td><b>Datum</b></td><td><b>Aufgabe</b></td><td><b>Aufwand</b></td></tr>")
        return out.getvalue()
        #return escape("<table>")
        # text = "|| '''Entwickler''' || '''Datum''' || '''Aufgabe''' || '''Aufwand''' ||"
        # Convert Wiki markup to HTML, new style
        #out = StringIO()
        #Formatter(formatter.context).format(text, out)
        #return Markup(out.getvalue())
