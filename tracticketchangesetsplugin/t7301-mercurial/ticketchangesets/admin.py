# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Mikael Relbe
# All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software. 
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
# ----------------------------------------------------------------------------

import re

from trac.admin import IAdminCommandProvider
from trac.core import *
from trac.util.text import printout

from ticketchangesets.api import *
from ticketchangesets.commit_updater import *

_oldmessage_pat = [
    # List of tuples (patstr, extract-fn) where
    # extract-fn in turn shall return a tuple (reponame, rev, message,
    # startcomment, endcomment)
    # matched with patstr

    # Message created by Trac 0.12 (tracopt.ticket.commit_updater):
    (r'^(?P<startcomment>.*?)\s*In \[.*?\]:\s+{{{\s*#!CommitTicketReference\s+'
     r'repository="(?P<reponame>.*?)"\s+revision="(?P<rev>[0-9]+)"\s+'
     r'(?P<message>.*?)\s+}}}\s*(?P<endcomment>.*?)$',
     lambda extract: (extract[1], extract[2], extract[3], extract[0],
                      extract[4])),

    # Message created by old custom script by mrelbe for Trac 0.11.x:
    (r'^{{{\s*#!div class="ticket-commit-message"\s+'
     r'\[(?P<rev>[0-9]+)\]:\s+(?P<message>.*?)\s+}}}\s*(?P<comment>.*?)$',
     lambda extract: ('', extract[0], extract[1], '', extract[2])),
    ]

_oldmessage_re = [(re.compile(pat, re.DOTALL), extract) for
                 pat, extract in _oldmessage_pat]

def _reformat_message(oldmessage):
    """Reformat old formatted message to current format.

    None is returned if no reformatting shall be done on provided message.
    """
    # Old message patterns and extract functions.
    # Lambda function is applied when ticket message matches pattern,
    # extracted tuple: (reponame, rev, message)
    matches = [(parts[0], extract) for parts, extract in
               [(pat.findall(oldmessage), extract) for
                pat, extract in _oldmessage_re] if parts]
    if matches:
        parts, extract = matches[0]
        reponame, rev, message, startcomment, endcomment = extract(parts)
        return make_ticket_comment(rev, message, reponame, startcomment,
                                   endcomment)

    
class TicketChangesetsAdmin(Component):
    """trac-admin command provider for ticketchangesets plugin."""

    implements(IAdminCommandProvider)

    # IAdminCommandProvider methods
    
    def get_admin_commands(self):
        yield ('ticket_changesets diff', '',
               """Examine ticket commit messages before reformat
               
               Generate a diff-like output for analysis before reformatting.
               The database will not be changed.
               
               Before this operation, you may want to run

               trac-admin $ENV repository resync "*"
               """,
               None, self.diff)
               
        yield ('ticket_changesets get', '[ticketid]',
               """Get a comma-separated list of related revisions.
               
               List format:
               #ticketid: rev/reponame,...
               
               "/reponame" is left out for the default repository.
               
               All tickets related to changesets are listed if ticketid is
               omitted (one ticket on each line). If no changeset relation
               exists, "None" is displayed.
               """,
               None, self.get_revs)
               
        yield ('ticket_changesets reformat', '',
               """Reformat ticket commit messages (DANGEROUS!)
               
               Before this operation, you may want to run:

               trac-admin $ENV repository resync "*"

               and then

               trac-admin $ENV ticket_changesets diff
               """,
               None, self.reformat)
               
        yield ('ticket_changesets resync', '',
               """Re-synchronize ticket changesets with all repositories
               
               Relations between tickets and changesets are re-built by
               examining all commit messages, in all repositories, for ticket
               references. Ticket comments are neither updated nor added due
               to new discoveries.
               
               Before this operation, you may want to run:

               trac-admin $ENV repository resync "*"
               """,
               None, self.resync)
               
    # Internal methods
    
    def diff(self):
        self._scan_ticket_commit_messages(False)
        
    def get_revs(self, tkt_id=None):
        r = {}
        if tkt_id is None:
            # Get tickets from db
            db = self.env.get_read_db()
            cursor = db.cursor()
            cursor.execute('SELECT ticket FROM ticket_changesets')
            for tkt_id, in cursor:
                csets = TicketChangesets(self.env).get(tkt_id)
                for (reponame, changesets) in csets:
                    r[tkt_id] = changesets.list_revs(reponame)
        else:
            csets = TicketChangesets(self.env).get(tkt_id)
            for (reponame, changesets) in csets:
                r[tkt_id] = changesets.list_revs(reponame)
        if r:
            for tkt_id, revs in r.iteritems():
                printout('#%s: %s' % (tkt_id, ','.join(revs)))
        else:
            printout('None')
            
    def reformat(self):
        self._scan_ticket_commit_messages(True)
        
    def resync(self):
        """Resync ticket changesets from commit messages in all repos.
        """
        printout('Resyncing ticket changesets...')
        ticket_changesets = TicketChangesets(self.env)
        ticket_updater = CommitTicketUpdater(self.env)
        repositories = RepositoryManager(self.env).get_real_repositories()
        n_changesets = 0

        @self.env.with_transaction()
        def do_clean(db):
            cursor = db.cursor()
            cursor.execute('DELETE FROM ticket_changesets')

        def _count_affected_tickets():
            db = self.env.get_read_db()
            cursor = db.cursor()
            cursor.execute('SELECT COUNT(*) FROM ticket_changesets')
            row = cursor.fetchone()
            return row and int(row[0]) or 0

        for repos in repositories:
            rev = repos.get_oldest_rev()
            while True:
                changeset = repos.get_changeset(rev)
                tickets = ticket_updater.parse_message(changeset.message)
                match = False
                for tkt_id, cmds in tickets.iteritems():
                    ticket_changesets.add(tkt_id, repos.id, rev)
                    match = True
                if match:
                    n_changesets += 1
                if rev == repos.get_youngest_rev():
                    break
                rev = repos.next_rev(rev)
        printout('Done, %d tickets related to %d changesets' %
                 (_count_affected_tickets(), n_changesets))

    def _scan_ticket_commit_messages(self, reformat=False):
        """Convert commit messages from old to new format. (DANGEROUS)"""

        if reformat:
            printout('Reformatting ticket commit messages...')
        else:
            printout('diff ticket commit messages to be reformatted')
        
        n_matches = [0]
                         
        @self.env.with_transaction()
        def do_update(db):
            cursor = db.cursor()
            # Iterate over current ticket comments
            cursor.execute('SELECT ticket,time,oldvalue,newvalue '
                           'FROM ticket_change WHERE field=%s', ['comment'])
            for row in cursor.fetchall():
                ticket, time, oldvalue, oldmessage = row
                if oldvalue.isnumeric(): # ticket comment number
                    newmessage = _reformat_message(oldmessage)
                    if newmessage:
                        n_matches[0] += 1
                        if reformat:
                            cursor.execute(
                                    'UPDATE ticket_change SET newvalue=%s '
                                    'WHERE ticket=%s and time=%s and '
                                    'oldvalue=%s',
                                    [newmessage, ticket, time, oldvalue])
                        else:
                            printout('@@ comment:%s:ticket:%d (db time %d) @@'
                                     % (oldvalue, ticket, time))
                            printout('-' + oldmessage.replace('\n', '\n-'))
                            printout('+' + newmessage.replace('\n', '\n+'))
            # Iterate over changed (edited) ticket comments
            cursor.execute('SELECT ticket,time,oldvalue,newvalue '
                           'FROM ticket_change WHERE field LIKE %s',
                           ['_comment_%'])
            for row in cursor.fetchall():
                ticket, time, oldmessage, edit_time = row
                if edit_time.isnumeric(): # ticket comment change time
                    newmessage = _reformat_message(oldmessage)
                    if newmessage:
                        n_matches[0] += 1
                        if reformat:
                            cursor.execute(
                                    'UPDATE ticket_change SET oldvalue=%s '
                                    'WHERE ticket=%s and time=%s and '
                                    'newvalue=%s',
                                    [newmessage, ticket, time, edit_time])
                        else:
                            printout('@@ comment:(edit):ticket:%d (db time %d) @@'
                                     % (ticket, edit_time))
                            printout('-' + oldmessage.replace('\n', '\n-'))
                            printout('+' + newmessage.replace('\n', '\n+'))
        if reformat:
            printout('%d messages reformatted' % n_matches[0])
        else:
            printout('%d messages to be reformatted' % n_matches[0])
            