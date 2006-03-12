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
    _keyword_split = re.compile(r'''[\w.-]+''')

    def __init__(self, env):
        self.env = env

    def _ticket_tags(self, ticket):
        return self._keyword_split.findall(ticket['keywords'])

    def _get_tags(self, *names):
        tags = set()
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = 'SELECT keywords FROM ticket'
        if names:
            sql += ' WHERE id IN (%s)' % ', '.join([int(n) for n in names])
        cursor.execute(sql)
        for row in cursor:
            tags.update(self._keyword_split.findall(row[0]))
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
            ticket.save_changes(req.authname, None)

    def replace_tags(self, tagspace, req, name, *tags):
        assert req.perm.assert_permission('TICKET_CHGPROP')
        ticket = model.Ticket(self.env, name)
        ticket['keywords'] = ' '.join(tags)
        ticket.save_changes(req.authname, None)

    def remove_tag(self, tagspace, req, name, tag):
        assert req.perm.assert_permission('TICKET_CHGPROP')
        ticket = model.Ticket(self.env, name)
        ticket['keywords'] = re.sub(r'\b%s\b' % tag, '', ticket['keywords'])
        ticket.save_changes(req.authname, None)

    def remove_all_tags(self, tagspace, req, name):
        assert req.perm.assert_permission('TICKET_CHGPROP')
        ticket = model.Ticket(self.env, name)
        del ticket['keywords']
        ticket.save_changes(req.authname, None)

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

