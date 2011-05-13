from trac.core import *
from trac.web.api import ITemplateStreamFilter

from genshi.builder import tag
from genshi.filters import Transformer

revision = "$Rev: 8149 $"
url = "$URL: http://svn.edgewall.org/repos/trac/tags/trac-0.12.2/sample-plugins/ticket_clone.py $"

class SimpleTicketCloneButton(Component):
    """Add a 'Clone' button to the ticket box. 
    
    This button is located next to the 'Reply' to description button,
    and pressing it will send a request for creating a new ticket
    which will be based on the cloned one.
    """
       
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html':
            ticket = data.get('ticket')
            if ticket and ticket.exists and \
                    'TICKET_CREATE' in req.perm(ticket.resource):
#                filter = Transformer('//h3[@id="comment:description"]')
                filter = Transformer('//h1[@id="trac-ticket-title"]')
                return stream | filter.after(self._clone_form(req, ticket, data))
        return stream

    def _clone_form(self, req, ticket, data):
        fields = {}
        for f in data.get('fields', []):
            name = f['name']
            if name == 'summary':
                fields['summary'] = "%s (geklont von %s)" % (ticket['summary'], ticket.id)
            elif name == 'description':
                fields['description'] = 'Geklont von Ticket <a href="%s/%s/ticket/%s">%s</a> (%s)<hr><br/> %s' % \
                    (self.env.project_url, self.env.project_name, 
                     ticket.id, ticket.id, ticket['summary'], ticket['description'])
            else:
                fields[name] = ticket[name]
        return tag.form(
            tag.div(
                tag.input(type="submit", name="clone", value="Klonen",
                    title="Create a copy of this ticket"),
                [tag.input(type="hidden", name='field_'+n, value=v) for n, v in
                    fields.items()],
                tag.input(type="hidden", name='preview', value=''),
                class_="inlinebuttons"),
            method="post", action=req.href.newticket())

