# -*- coding: utf-8 -*-
from genshi.core import Attrs, QName
from genshi.filters.transform import ENTER, Transformer
from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter
from trac.wiki.api import IWikiChangeListener

class FieldTooltip(Component):
    implements(ITemplateStreamFilter, IWikiChangeListener)

    def __init__(self):
        # TODO: retrieve initial wiki contents for field help as follows:
        self.pages = {  'reporter': 'The author of the ticket.',
                        'type': 'The nature of the ticket (for example, defect or enhancement request). See TicketTypes for more details.',
                        'component': 'The project module or subsystem this ticket concerns.',
                        'version': 'Version of the project that this ticket pertains to.',
                        'keywords': 'Keywords that a ticket is marked with. Useful for searching and report generation.',
                        'priority': 'The importance of this issue, ranging from trivial to blocker. A pull-down if different priorities where defined.',
                        'milestone': 'When this issue should be resolved at the latest. A pull-down menu containing a list of milestones.',
                        'assigned to': 'Principal person responsible for handling the issue.',
                        'owner': 'Principal person responsible for handling the issue.',
                        'cc': 'A comma-separated list of other users or E-Mail addresses to notify. Note that this does not imply responsiblity or any other policy.',
                        'resolution': 'Reason for why a ticket was closed. One of fixed, invalid, wontfix, duplicate, worksforme.',
                        'status': 'What is the current status? One of new, assigned, closed, reopened.',
                        'summary': 'A brief description summarizing the problem or issue. Simple text without WikiFormatting.',
                        'description': 'The body of the ticket. A good description should be specific, descriptive and to the point. Accepts WikiFormatting.'}
        self.ticket_transformer = Transformer()
        self.ticket_transformer = self.ticket_transformer.select('//label').apply(self._TitleAdder(self.pages, 'for', 'field-')).end()
        self.ticket_transformer = self.ticket_transformer.select('//th').apply(self._TitleAdder(self.pages, 'id', 'h_')).end()

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html': 
            return stream | self.ticket_transformer
        return stream


    class _TitleAdder(object):

        def __init__(self, pages, attr_name, prefix=''):
            self.pages = pages
            self.attr_name = attr_name
            self.prefix = prefix

        def __call__(self, stream):
            for mark, (kind, data, pos) in stream:
                if mark is ENTER:
                    name = data[1].get(self.attr_name)
                    if name and name.startswith(self.prefix):
                        name = name[len(self.prefix):]
                    if name in self.pages:
                        attrs = data[1] | [(QName('title'), name + ': ' + self.pages.get(name))]
                        data = (data[0], attrs)
                yield mark, (kind, data, pos)

