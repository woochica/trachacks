from trac.core import *
from tractags.api import ITaggingSystemProvider, TaggingSystem, sorted, set
from trac.ticket.query import Query
from trac.ticket import model
import re

class TicketTaggingSystem(TaggingSystem):
    _keyword_split = re.compile(r'''\w[\w.@-]+''')

    # These builtin fields can be used as tag sources
    _builtin_fields = ('component', 'severity', 'priority', 'owner',
                       'reporter', 'cc', 'version', 'milestone', 'status',
                       'resolution', 'summary', 'description', 'keywords')

    def __init__(self, env):
        self.env = env
        self.fields = [x.strip() for x in self.env.config.get('tags.ticket',
                       'fields', 'keywords').split(',') if x.strip()
                       and x.strip() in self._builtin_fields]
        self.custom_fields = [x.strip() for x in self.env.config.get('tags.ticket',
                              'custom_fields', '').split(',') if x.strip()]

    def _ticket_tags(self, ticket):
        return set(self._keyword_split.findall(' '.join([ticket[f] for f in self.fields])))

    def walk_tagged_names(self, names, tags, predicate):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        tags = set(tags)
        names = set(names)
        args = []
        sql = "SELECT * FROM (SELECT id, %s, %s AS allfields FROM ticket) s" % (','.join(self.fields),
            '||'.join(["COALESCE(%s, '')" % f for f in self.fields]))
        constraints = []
        if names:
            constraints.append("id IN (" + ', '.join(['%s' for n in names]) + ")")
            args += [unicode(n) for n in names]
        if tags:
            constraints.append("(" + ' OR '.join(["allfields LIKE %s" for t in tags]) + ")")
            args += ['%' + t + '%' for t in tags]
        if constraints:
            sql += " WHERE " + " AND ".join(constraints)
        sql += " ORDER BY id"
        cursor.execute(sql, args)
        for row in cursor:
            id, ttags = row[0], ' '.join([f for f in row[1:-1] if f])
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
        summary = ticket['summary'] or u''
        return (href, wiki_to_oneliner('#%s' % name, self.env),
                ticket.exists and summary)

class TicketTags(Component):
    """ Export a ticket tag interface, using the "keywords" field of tickets. """
    implements(ITaggingSystemProvider)

    def get_tagspaces_provided(self):
        yield 'ticket'

    def get_tagging_system(self, tagspace):
        return TicketTaggingSystem(self.env)

