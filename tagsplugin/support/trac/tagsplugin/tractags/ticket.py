from trac.core import *
from tractags.api import ITaggingSystemProvider, TaggingSystem
from trac.ticket.query import Query
from trac.ticket import model
import re

try:
    set = set
except:
    from sets import Set as set

class TicketTaggingSystem(TaggingSystem):
    def __init__(self, env):
        self.env = env

    def _ticket_tags(self, ticket):
        return ticket['keywords'].split()

    def _get_tags(self, *names):
        tags = set()
        if names:
            for name in names:
                ticket = model.Ticket(self.env, name)
                tags.update(self._ticket_tags(ticket))
        else:
            query = Query(self.env)
            for ticket in query.execute():
                ticket = model.Ticket(self.env, ticket['id'])
                tags.update(self._ticket_tags(ticket))
        return tags
        
    def _get_tagged(self, *tags):
        tags = set(tags)
        if tags:
            query = Query.from_string(self.env, "keywords=~%s" % '|'.join(tags))
        else:
            query = Query.from_string(self.env, "keywords!=")

        for ticket in query.execute():
            ticket = model.Ticket(self.env, ticket['id'])
            ttags = set(self._ticket_tags(ticket))
            if not tags and ttags or tags.intersection(ttags):
                yield ticket

    def get_tagged_names(self, tagspace, *tags):
        return [ticket.id for ticket in self._get_tagged(*tags)]

    def get_tags(self, tagspace, *names):
        return self._get_tags(*names)

    def add_tag(self, tagspace, req, name, tag):
        assert req.perm.assert_permission('TICKET_CHGPROP')
        ticket = model.Ticket(self.env, name)
        tags = self._ticket_tags(ticket)
        if tag not in tags:
            ticket['keywords'] = '%s %s' % (ticket['keywords'], tag)
            ticket.save_changes(req.authname, 'added tag %s' % tag)

    def remove_tag(self, tagspace, req, name, tag):
        assert req.perm.assert_permission('TICKET_CHGPROP')
        ticket = model.Ticket(self.env, name)
        ticket['keywords'] = re.sub(r'\b%s\b' % tag, '', ticket['keywords'])
        ticket.save_changes(req.authname, 'removed tag %s' % tag)

    def remove_all_tags(self, tagspace, req, name):
        assert req.perm.assert_permission('TICKET_CHGPROP')
        ticket = model.Ticket(self.env, name)
        del ticket['keywords']
        ticket.save_changes(req.authname, 'all tags removed')

    def name_link(self, tagspace, name):
        ticket = model.Ticket(self.env, name)
        return (self.env.href.ticket(name), '#%s' % name, ticket.exists and ticket['summary'])

class TicketTags(Component):
    """ Export a ticket tag interface, using the "keywords" field of tickets. """
    implements(ITaggingSystemProvider)

    def get_tagspaces_provided(self):
        yield 'ticket'

    def get_tagging_system(self, tagspace):
        return TicketTaggingSystem(self.env)

