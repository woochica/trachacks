# TicketBackLinks plugin for Trac Tickets
# Version: 0.1
#
# David Francos Cuartero
# Based on Trapanator <trap@trapanator.com>'s BackLinks plugin
# ( http://www.trapanator.com/blog/archives/category/trac)
# and http://trac.edgewall.org/wiki/TracTicketsCustomFields
# License: GPL 3.0


import string
from StringIO import StringIO
from genshi.builder import tag
from genshi.filters import Transformer
from trac.wiki.macros import WikiMacroBase
from trac.core import *
from trac.config import Option
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider
from trac.util import TracError
from trac.util.text import to_unicode
from trac.wiki.model import WikiPage
from trac.mimeview.api import Mimeview, get_mimetype, Context, WikiTextRenderer

class TicketBackLinksMacro(WikiMacroBase):
    revision = "$Rev$"
    url = "$URL$"

    def expand_macro(self, formatter, name, args):
	"""
		Shows links to pages referring to a ticket in a ticket's description.
		You can call it from anywhere, like TicketBackLinks[ticketid] .
	"""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        thispage = None
        context = formatter.context
        resource = context.resource
        if args:
                thispage = args.replace('\'', '\'\'')
        else:
       	        thispage = WikiPage(self.env, resource).name

        sql = 'SELECT w1.name FROM wiki w1, ' + \
                  '(SELECT name, MAX(version) AS VERSION FROM WIKI GROUP BY NAME) w2 ' + \
                  'WHERE w1.version = w2.version AND w1.name = w2.name '
	sql += 'AND ( w1.text LIKE \'%%[ticket:%s]%%\' ' % thispage
	sql += 'OR w1.text LIKE \'%%#%s %%\' )' % thispage


        cursor.execute(sql)
        buf = StringIO()

	firsttime = 1

	for page in cursor.fetchall():
		if page == None:
			break
		if page == thispage:
			pass
		else:
			if firsttime != 0:
				buf.write('<h3 id="comment:description"> Mentioned in:</h3><ul>')
			buf.write('<li><a href="%s">%s</a></li>' % (self.env.href.wiki(page[0]),page[0]))
			firsttime = 0
	buf.write('</ul>')
	return buf.getvalue()
 
class TicketBackLinksDescription(Component):
    implements(ITemplateStreamFilter, ITemplateProvider)

    def filter_stream(self, req, method, filename, stream, data):
        if filename != 'ticket.html':
            return stream
	ticket = data['ticket']
	id = ticket.id
	try:
		int(id) 
		isint=1
	except: 
		isint=0

	if isint == 1:

		content="[[TicketBackLinks(%d)]]" %ticket.id
		content = WikiTextRenderer(self.env).render(Context.from_request(req), 'text/x-trac-wiki', content)
	        stream |= Transformer("//div[@class='description']").after(tag.div(content, **{'class': "description" }))

	return stream

    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        return []

