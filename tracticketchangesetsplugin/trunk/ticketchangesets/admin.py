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

from .api import *
from .commit_updater import *

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
        print('Done, %d tickets related to %d changesets' %
              (_count_affected_tickets(), n_changesets))

    def _scan_ticket_commit_messages(self, reformat=False):
        """Convert commit messages from old to new format. (DANGEROUS)"""

        if reformat:
            printout('Reformatting ticket commit messages...')
        else:
            printout('diff ticket commit messages to be reformatted')
        
        # Old message patterns and extract functions.
        # Lambda function is applied when ticket message matches pattern,
        # extracted tuple: (reponame, rev, message)
        oldmessage_pat = [
            
            # Message created by Trac 0.12 (tracopt.ticket.commit_updater):
            (r'^In \[.*?\]:\s+{{{\s*#!CommitTicketReference\s+'
             r'repository="(?P<reponame>.*?)"\s+revision="(?P<rev>[0-9]+)"\s+'
             r'(?P<message>.*?)\s+}}}$',
             lambda extract: (extract[0], extract[1], extract[2])),
            
            # Message created by old custom script by mrelbe for Trac 0.11.x:
            (r'^{{{\s*#!div class="ticket-commit-message"\s+'
             r'\[(?P<rev>[0-9]+)\]:\s+(?P<message>.*?)\s+}}}$',
             lambda extract: ("", extract[0], extract[1])),
        ]

        oldmessage_re = [(re.compile(pat, re.DOTALL), extract) for 
                         pat, extract in oldmessage_pat]
        n_matches = [0]
                         
        @self.env.with_transaction()
        def do_update(db):
            cursor = db.cursor()
            # Iterate over all ticket comments
            cursor.execute('SELECT rowid,ticket,oldvalue,newvalue '
                           'FROM ticket_change WHERE field=%s', ['comment'])
            for row in cursor.fetchall():
                rowid, ticket, oldvalue, oldmessage = row
                if oldvalue.isnumeric(): # ticket comment number
                    matches = [(parts[0], extract) for parts, extract in 
                               [(pat.findall(oldmessage), extract) for
                                pat, extract in oldmessage_re] if parts]
                    if matches:
                        n_matches[0] += 1
                        parts, extract = matches[0]
                        reponame, rev, message = extract(parts)
                        newmessage = make_ticket_comment(rev, message)
                        if reformat:
                            cursor.execute('UPDATE ticket_change '
                                           'SET newvalue=%s WHERE rowid=%s',
                                           [newmessage, rowid])
                        else:
                            printout('@@ comment:%s:ticket:%s (db rowid %s) @@'
                                     % (oldvalue, ticket, rowid))
                            printout('-' + oldmessage.replace('\n', '\n-'))
                            printout('+' + newmessage.replace('\n', '\n+'))
        if reformat:
            printout('%d messages reformatted' % n_matches[0])
        else:
            printout('%d messages to be reformatted' % n_matches[0])
            