from trac.core import *
from tractags.api import ITaggingSystemProvider, TaggingSystem
from trac.ticket.query import Query
from trac.ticket import model
from trac.util import sorted
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
        return set(self._keyword_split.findall(ticket['keywords']))

    def walk_tagged_names(self, names, tags, predicate):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        tags = set(tags)
        names = set(names)
        args = []
        sql = "SELECT id, keywords FROM ticket WHERE keywords IS NOT NULL AND keywords != ''"
        if names:
            sql += " AND id IN (" + ', '.join(['%s' for n in names]) + ")"
            args += [unicode(n) for n in names]
        if tags:
            sql += " AND (" + ' OR '.join(["keywords LIKE %s" for t in tags]) + ")"
            args += ['%' + t + '%' for t in tags]
        sql += " ORDER BY id"
        cursor.execute(sql, args)
        for id, ttags in cursor:
            ticket_tags = set(self._keyword_split.findall(ttags))
            if not tags or ticket_tags.intersection(tags):
                if predicate(id, ticket_tags):
                    yield (id, ticket_tags)
                
    def get_name_tags(self, name):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT keywords FROM ticket WHERE id=%s AND keywords IS NOT NULL AND keywords != ''", (name,))
        for row in cursor:
            return set(self._keyword_split.findall(row[0]))

    def add_tags(self, req, name, tags):
        ticket = model.Ticket(self.env, name)
        ticket_tags = self._ticket_tags(ticket)
        ticket_tags.update(tags)
        ticket['keywords'] = ' '.join(sorted(ticket_tags))
        ticket.save_changes(req.authname, None)

    def replace_tags(self, req, name, tags):
        ticket = model.Ticket(self.env, name)
        ticket['keywords'] = ' '.join(sorted(tags))
        ticket.save_changes(req.authname, None)

    def remove_tags(self, req, name, tags):
        ticket = model.Ticket(self.env, name)
        ticket_tags = self._ticket_tags(ticket)
        ticket_tags.symmetric_difference_update(tags)
        ticket['keywords'] = ' '.join(sorted(ticket_tags))
        ticket.save_changes(req.authname, None)

    def remove_all_tags(self, req, name):
        ticket = model.Ticket(self.env, name)
        ticket['keywords'] = ''
        ticket.save_changes(req.authname, None)

    def name_details(self, name):
        ticket = model.Ticket(self.env, name)
        href = self.env.href.ticket(name)
        from trac.wiki.formatter import wiki_to_oneliner
        return (href, wiki_to_oneliner('#%s' % name, self.env),
                ticket.exists and ticket['summary'] or '')

class TicketTags(Component):
    """ Export a ticket tag interface, using the "keywords" field of tickets. """
    implements(ITaggingSystemProvider)

    def get_tagspaces_provided(self):
        yield 'ticket'

    def get_tagging_system(self, tagspace):
        return TicketTaggingSystem(self.env)

