from trac.core import *
from trac.web.api import ITemplateStreamFilter

from genshi.builder import tag
from genshi.filters import Transformer

revision = "$Rev$"
url = "$URL$"

class TicketCreateButtons(Component):
    """Add a buttons to the ticket box to create related tickets which
    inherit some values from the current ticket.
    
    The [tickets-create-buttons] section of trac.ini can be used to
    add buttons which create a new ticket based on the current
    ticket.  The plugin handles all *.tag values in that section.  The
    values are as follows:

    tag : An argument to genshi.filters.Transfomer used to find the
      ticket form element to which the button will be prepended.
      Typically this is a custom field name.  For example,
      .//td[@headers="h_blockedby"] for the MasterTickets blockedBy
      field.
    label : The label for the button (e.g., "Create")
    title : The HTML title element used as a tool tip for the button

    inherit : A comma-separated list of fields whose values should be
      inherited from the current ticket.  If not present, all fields
      are inherited.  if present but blank, no fields are inherited.
      Otherwise, the listed fields are inherited.
    
    link : A comma-separated list of pairs of fields used to link the
      two tickets.  Each element is in the form newfield:currentfield.
      For example, blockedby:id sets the new ticket's blockedby field
      to the current tickets id.  link fields override inherited
      fields.

    set : A comma-separated list of field:value pairs for setting
      values in the new ticket.  For example, keywords:Foo sets the
      new ticket's keywords field to Foo. set fields override
      inherited and link field.

    Example:

    [ticket-create-buttons]
    blocking.tag = .//td[@headers="h_blocking"]
    blocking.label = Create
    blocking.title = Create a new successor
    blocking.inherit = type, owner, reporter, milestone, component
    blocking.link = blockedby:id
    blocking.set = keywords:Foo
    """
       
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html':
            ticket = data.get('ticket')
            if ticket and ticket.exists and \
                    'TICKET_CREATE' in req.perm(ticket.resource):
                # Find the configured buttons (anything in
                # [ticket-create-buttons] that has a name like "*.tag")
                options=self.config.options('ticket-create-buttons')
                buttons=[]
                for n, v in options:
                    p=n.split('.')
                    if len(p)==2 and p[1] == 'tag':
                        buttons.append(p[0])

                # Create the configured buttons
                for b in buttons:
                    tag=self.config.get('ticket-create-buttons','%s.tag' % b)
                    filter = Transformer(tag)
                    stream = stream | filter.prepend(self._create_button(b, req, ticket, data))
        return stream

    def _create_button(self, b, req, ticket, data):
        # Text for button
        label=self.config.get('ticket-create-buttons','%s.label' % b)
        title=self.config.get('ticket-create-buttons','%s.title' % b)

        # Field values for new ticket
        fields = {}

        # Values inherited from the current ticket
        # No setting: all, blank setting: none, Otherwise: the fields listed
        inherit=self.config.getlist('ticket-create-buttons',
                                    '%s.inherit' % b, 
                                    default=data.keys())
        for f in inherit:
            fields[f]=ticket[f]

        # Fields that link the new ticket to the current ticket
        # Missing or empty, no links.
        link=self.config.getlist('ticket-create-buttons','%s.link' % b, default=[])
        for l in link:
            to, fr = l.split(':')
            if fr == 'id':
                fields[to] = ticket.id
            else:
                fields[to]=ticket[fr]

        # Specific value assignments.  E.g., a button could always create a test
        set=self.config.getlist('ticket-create-buttons','%s.set' % b, default=[])
        for s in set:
            n, v = s.split(':')
            fields[n]=v

        # Build the form with the values set up above.
        return tag.form(
            tag.div(
                tag.input(type="submit", name="create_"+b, value=label,
                          title=title),
                # With name='field_'+n here the field prefilled for post but not for get
                [tag.input(type="hidden", name=n, value=v) for n, v in
                 fields.items()],
                class_="inlinebuttons"),
            # With "post" here instead of "get" the ticket is previewed and 
            # we get a warning about the missing summary.
            method="get", action=req.href.newticket())
