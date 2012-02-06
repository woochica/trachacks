from trac.web.api import ITemplateStreamFilter

from genshi.builder import tag
from genshi.filters import Transformer
from trac.util.translation import domain_functions
from trac.config import Option
from pkg_resources import resource_filename #@UnresolvedImport
from trac.core import Component, implements

_, tag_, N_, add_domain = domain_functions('ticketnav', '_', 'tag_', 'N_', 'add_domain')

class SimpleTicketCloneButton(Component):
    """Add a 'Clone' button to the ticket box. 

~~This button is located next to the 'Reply' to description button,
and~~ pressing it will send a request for creating a new ticket
which will be based on the cloned one.

Copied from both `trac-0.12.2/sample-plugins/ticket_clone.py` 
and from `TRAC/tracopt/ticket/clone.py`. Adjusted position 
of Clone-Button and translated text. 
"""
       
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter methods
    xpathToPosition = Option('trac', 'clone_xpath', '//h1[@id="trac-ticket-title"]', 
                             """xpath to postion of clone button""")

    def __init__(self):
            # bind the 'tracnav' catalog to the locale directory 
            locale_dir = resource_filename(__name__, 'locale') 
            add_domain(self.env.path, locale_dir)
        
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html':
            ticket = data.get('ticket')
            if ticket and ticket.exists and \
                    'TICKET_CREATE' in req.perm(ticket.resource):
#                filter = Transformer('//h3[@id="comment:description"]')
                filter = Transformer( self.config.get('trac', 'clone_xpath') )
                return stream | filter.after(self._clone_form(req, ticket, data))
        return stream

    def _clone_form(self, req, ticket, data):
        fields = {}
        for f in data.get('fields', []):
            name = f['name']
            if name == 'summary':
#                fields['summary'] = "%(summary)s (geklont von %s)" % (ticket['summary'], ticket.id)
                fields['summary'] = _("%(summary)s (cloned from %(id)s)",
                                  summary=ticket['summary'], id=ticket.id)
            elif name == 'description':
                fields['description'] = \
                    _("Cloned from #%(id)s:\n----\n%(description)s",
                      id=ticket.id, description=ticket['description'])
            else:
                fields[name] = ticket[name]
        return tag.form(
            tag.div(
                tag.input(type="submit", name="clone", value=_('Clone'),
                    title=_('Create a copy of this ticket')),
                [tag.input(type="hidden", name='field_'+n, value=v) for n, v in
                    fields.items()],
                tag.input(type="hidden", name='preview', value=''),
                class_="inlinebuttons"),
            method="post", action=req.href.newticket())