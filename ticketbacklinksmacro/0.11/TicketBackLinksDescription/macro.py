# TicketBackLinks plugin for Trac Tickets
#
# David Francos Cuartero
# Based on Trapanator <trap@trapanator.com>'s BackLinks plugin
# and http://trac.edgewall.org/wiki/TracTicketsCustomFields
# License: GPL 3.0

from genshi.builder import tag
from genshi.filters import Transformer
from trac.core import Component, implements
from trac.mimeview.api import Context, WikiTextRenderer
from trac.web.api import ITemplateStreamFilter
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage

from StringIO import StringIO

class TicketBackLinksMacro(WikiMacroBase):

    def expand_macro(self, formatter, name, args):
        """Shows links to pages referring to a ticket in a ticket's description.
        You can call it from anywhere, like TicketBackLinks[ticketid] .
        """ 
        if args:
            thispage = args.replace('\'', '\'\'')
        else:
            thispage = WikiPage(self.env, formatter.context.resource).name

        sql = """SELECT w1.name FROM wiki w1,
                (SELECT name, MAX(version) AS VERSION FROM wiki GROUP BY NAME) w2
                 WHERE w1.version = w2.version AND w1.name = w2.name """
        sql += 'AND ( w1.text LIKE \'%%[ticket:%s]%%\' ' % thispage
        sql += 'OR w1.text LIKE \'%%#%s %%\' )' % thispage
        sql += 'AND ( w1.text LIKE \'%%[ticket:%s]%%\' ' % thispage
        sql += 'OR (w1.text LIKE \'%%#%s%%\' )' % thispage
        sql += 'AND w1.text NOT LIKE \'%%#%s0%%\'' % thispage
        sql += 'AND w1.text NOT LIKE \'%%#%s1%%\'' % thispage
        sql += 'AND w1.text NOT LIKE \'%%#%s2%%\'' % thispage
        sql += 'AND w1.text NOT LIKE \'%%#%s3%%\'' % thispage
        sql += 'AND w1.text NOT LIKE \'%%#%s4%%\'' % thispage
        sql += 'AND w1.text NOT LIKE \'%%#%s5%%\'' % thispage
        sql += 'AND w1.text NOT LIKE \'%%#%s6%%\'' % thispage
        sql += 'AND w1.text NOT LIKE \'%%#%s7%%\'' % thispage
        sql += 'AND w1.text NOT LIKE \'%%#%s8%%\'' % thispage
        sql += 'AND w1.text NOT LIKE \'%%#%s9%%\' )' % thispage

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(sql)

        buf = StringIO()

        buf.write('<h3 id="comment:description"> Mentioned in:</h3><ul>')
        for page, in cursor:
            if page and page != thispage:
                buf.write('<li><a href="%s">%s</a></li>' % (self.env.href.wiki(page), page))
        buf.write('</ul>')
        
        return buf.getvalue()

class TicketBackLinksDescription(Component):

    implements(ITemplateStreamFilter)

    def filter_stream(self, req, method, filename, stream, data):
        if filename != 'ticket.html' and (filename != 'typedticket.html'):
            return stream
        ticket = data['ticket']
        id = ticket.id
        try:
            int(id)
            isint = 1
        except:
            isint = 0

        if isint == 1:
            content = "[[TicketBackLinks(%d)]]" % ticket.id
            content = WikiTextRenderer(self.env).render(Context.from_request(req), 'text/x-trac-wiki', content)
            stream |= Transformer("//div[@class='description']").after(tag.div(content, **{'class': "description" }))

        return stream
