import os
import re
import pickle
from StringIO import StringIO
from trac.core import *
from trac.config import Option
from trac.perm import IPermissionRequestor
from trac.ticket.model import Ticket, Priority
from trac.ticket.query import Query
from trac.resource import ResourceNotFound
from trac.util import sorted, escape
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.wiki.formatter import system_message, wiki_to_oneliner
from trac.wiki.macros import WikiMacroBase

class Poll(object):
    def __init__(self, base_dir, title, vote_defs):
        self.vote_defs = vote_defs
        self.title = title
        # Perhaps the Wiki page name should be included?
        self.key = ''.join(re.findall(r'(\w+)', title ,re.UNICODE)).lower()
        self.store = os.path.join(base_dir, self.key + '.poll')
        self.load()

    def load(self):
        """ Load pickled representation of votes. """
        self.votes = {}
        if os.path.isfile(self.store):
            fd = open(self.store, 'r')
            try:
                poll = pickle.load(fd)
            finally:
                fd.close()
            assert self.title == poll['title'], \
                   'Stored poll is not the same as this one.'
            self.votes = dict([(k, v) for k, v in poll['votes'].iteritems()
                               if k in [d[0] for d in self.vote_defs]])
        self.votes.update(dict([(k[0], []) for k in self.vote_defs
                                if k[0] not in self.votes]))

    def save(self):
        data = {'title': self.title,
                'votes': self.votes}
        if not os.path.exists(os.path.dirname(self.store)):
            raise TracError('Vote path %s does not exist.' % self.store)
        fd = open(self.store, 'w')
        try:
            pickle.dump(data, fd)
        finally:
            fd.close()

    def populate(self, req):
        """ Update poll based on HTTP request. """
        if req.args.get('poll', '') == self.key:
            vote = req.args.get('vote', '')
            if not vote:
                return
            if vote not in self.votes:
                raise TracError('No such vote %s' % vote)
            username = req.authname or 'anonymous'
            for v, voters in self.votes.items():
                if username in voters:
                    self.votes[v].remove(username)
            self.votes[vote] = self.votes[vote] + [username]
            self.save()

    def render(self, env, req):
        out = StringIO()
        can_vote = req.perm.has_permission('POLL_VOTE')
        if can_vote:
            out.write('<form id="%(id)s" method="get" action="%(href)s#%(id)s">\n'
                      '<input type="hidden" name="poll" value="%(id)s"/>\n'
                      % {'id': self.key, 'href': env.href(req.path_info)})
        out.write('<fieldset class="poll">\n'
                  ' <legend>%s</legend>\n'
                  ' <ul>\n'
                  % escape(self.title))
        username = req.authname or 'anonymous'
        for id, style, vote in self.vote_defs:
            hid = escape(str(id))
            out.write('<li%s>\n' % (style and ' class="%s"' % style or ''))
            if can_vote:
                checked = username in self.votes[id]
                out.write('<input type="radio" name="vote" id="%(pvid)s" value="%(vid)s"%(checked)s/>\n'
                          '<label for="%(pvid)s">%(vote)s</label>\n'
                          % {'vid': hid,
                             'pvid': self.key + hid,
                             'vote': vote,
                             'checked': checked and ' checked="checked"' or ''})
            else:
                out.write(vote)
            if self.votes[id]:
                out.write(' <span class="voters">(<span class="voter">' +
                          '</span>, <span class="voter">'.join(self.votes[id]) +
                          '</span>)</span>')
            out.write('</li>\n')
        can_vote and out.write('<input type="submit" value="Vote"/>')
        out.write(' </ul>\n</fieldset>\n')
        can_vote and out.write('</form>\n')
        return out.getvalue()


class PollMacro(WikiMacroBase):
    """ Add a poll. Each argument must be separated by a semi-colon (;) or 
    new-line (if used as a processor). The first argument is the title of the
    poll, which is also the identifier for each poll.
    
    Usage: `[[Poll(<title>; <arg> [; <arg>] ...)]]`

    Where <arg> conforms to the following:

        || '''<arg>'''            || '''Description''' ||
        || `query:<ticket-query>` || Add tickets from a query to the poll. ||
        || `#<n>`                 || Add an individual ticket to the poll. ||
        || `<text>`               || A poll question. ||

    eg.

    [[Poll(Which of these do you prefer?; #1; #2; #3; query:component=Request-a-Hack&status!=closed; Cheese dip)]]
    """

    implements(IPermissionRequestor, ITemplateProvider)

    base_dir = Option('poll', 'base_dir', '/tmp',
                      'Path where poll pickle dumps should be stored.')

    def expand_macro(self, formatter, name, content):
        req = formatter.req
        if not content:
            return system_message("A title must be provided as the first argument to the poll macro")
        content = filter(None, [i.strip() for i in
                                content.replace(';', '\n').split('\n')])
        if len(content) < 2:
            return system_message("One or more options must be provided to vote on.")
        title = content.pop(0)
        return self.render_poll(req, title, content)

    def render_poll(self, req, title, votes):
        add_stylesheet(req, 'poll/css/poll.css')
        if not req.perm.has_permission('POLL_VIEW'):
            return ''

        all_votes = []
        ticket_count = 0
        for vote in votes:
            tickets = []
            if vote.startswith('#'):
                try:
                    tickets.append(int(vote.strip('#')))
                except ValueError:
                    raise TracError('Invalid ticket number %s' % vote)
            elif vote.startswith('query:'):
                query = vote[6:]
                tickets = [q['id'] for q in
                           Query.from_string(self.env, query).execute(req)]
            else:
                all_votes.append(('%08x' % abs(hash(vote)), None,
                                 wiki_to_oneliner(vote, self.env, req=req)))

            # Make tickets look pretty
            for idx, id in enumerate(tickets):
                try:
                    ticket = Ticket(self.env, id)
                except Exception:
                    continue
                summary = ticket['summary'] + ' (#%i)' % id
                try:
                    priority = Priority(self.env, ticket['priority']).value
                except ResourceNotFound, e: #this priority name has been removed from model
                    priority = 0
                summary = wiki_to_oneliner(summary, self.env, req=req)

                all_votes.append((str(id), "ticket prio%s%s%s" %
                                  (priority, ticket_count % 2 and ' even' or '',
                                  ticket['status'] == 'closed' and ' closed' or ''),
                                  summary))
                ticket_count += 1

        if not all_votes:
            raise TracError('No votes provided')

        poll = Poll(self.base_dir, title, all_votes)
        if req.perm.has_permission('POLL_VOTE'):
            poll.populate(req)
        return poll.render(self.env, req)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ('POLL_VIEW',
                ('POLL_VOTE', ('POLL_VIEW',)))

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('poll', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
