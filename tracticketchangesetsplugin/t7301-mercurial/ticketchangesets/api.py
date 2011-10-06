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

from trac.versioncontrol.api import RepositoryManager
from trac.wiki.formatter import format_to_oneliner

from ticketchangesets.translation import _


class TicketChangesets(object):
    """Handle changesets recorded for a ticket.
    """

    def __init__(self, env):
        self.env = env

    def _read(self, tkt_id, repo_id):
        """Get ticket changesets from db"""
        db = self.env.get_read_db()
        cursor = db.cursor()
        cursor.execute('SELECT value FROM ticket_changesets '
                       'WHERE ticket=%s AND repository=%s',
                       [tkt_id, repo_id])
        row = cursor.fetchone()
        if row:
            changesets = Changesets(row[0])
            return changesets
        else:
            return Changesets()

    def _write(self, tkt_id, repo_id, changesets):
        """Write ticket changesets to db"""
        @self.env.with_transaction()
        def do_update(db):
            cursor = db.cursor()
            value = str(changesets)
            if changesets.exists:
                if value:
                    cursor.execute('UPDATE ticket_changesets SET value=%s '
                                   'WHERE ticket=%s AND repository=%s',
                                   [value, tkt_id, repo_id])
                else:
                    cursor.execute('DELETE FROM ticket_changesets '
                                   'WHERE ticket=%s AND repository=%s',
                                   [tkt_id, repo_id])
            elif value:
                cursor.execute('INSERT INTO ticket_changesets '
                               '(ticket,repository,value) VALUES(%s,%s,%s)',
                               [tkt_id, repo_id, value])
    
    def add(self, tkt_id, repo_id, rev):
        changesets = self._read(tkt_id, repo_id)
        self.env.log.debug('ticketchangesets: Add rev %s to #%d' %
                           (rev, tkt_id))
        changesets.add(rev)
        self._write(tkt_id, repo_id, changesets)

    def remove(self, tkt_id, repo_id, rev):
        changesets = self._read(tkt_id, repo_id)
        self.env.log.debug('ticketchangesets: Remove rev %s from #%d' %
                           (rev, tkt_id))
        changesets.remove(rev)
        self._write(tkt_id, repo_id, changesets)

    def get(self, tkt_id):
        """Return a sorted list of tuples (reponame, changesets) for a ticket.
        """
        changesets = [] # [(reponame, Changesets)]
        repos = RepositoryManager(self.env).get_real_repositories()

        for repo in sorted(repos, key=lambda r: r.reponame):
            c = self._read(tkt_id, repo.id)
            if c.exists:
                changesets.append((repo.reponame, c))
        return changesets


class Changesets(object):
    """Manipulates and formats changesets, stored on string format, for one
    repository and ticket.
    
    Format: comma separated numbers "a,b,c,d,..."
    """
    def __init__(self, revs=None):
        """revs is a comma separated list of revs"""
        self.exists = revs is not None
        if revs:
            try:
                self.revs = [str(x) for x in revs.split(',')]
            except:
                try:
                    self.revs = [str(self.revs)]
                except:
                    self.revs = []
        else:
            self.revs = []

    def __str__(self):
        return ','.join([str(r) for r in self.revs])

    def get_compact(self):
        """Returns a compacted sequence of revisions.
        
        Example: 1,2,3,5,6,7 compacts to 1-3,5-7
        """
        c = []
        m = len(self.revs)
        a = self.revs[0]
        i = 1
        while i <= m:
            if i == m or self.revs[i-1]+1 < self.revs[i]:
                if a == self.revs[i-1]:
                    c += [a]
                else:
                    c += ["%s-%s" % (a, self.revs[i-1])]
                if i < m:
                    a = self.revs[i]
            i += 1
        return c

    def add(self, rev):
        if not rev in self.revs:
            self.revs.append(str(rev))
            self.revs.sort()

    def remove(self, rev):
        try:
            self.revs.remove(str(rev))
        except:
            pass

    def list_revs(self, reponame):
        """Make list of revisions for a given repo"""
        r = self.revs
        if reponame and reponame != '(default)':
            return ['%s/%s' % (c, reponame) for c in r]
        else:
            return ['%s' % c for c in r]

    def wiki_revs(self, reponame, compact):
        """Make wiki text of revisions for a given repo"""
        if compact:
            r = self.get_compact()
        else:
            r = self.revs
        if reponame and reponame != '(default)':
            return ' '.join(['[%s/%s]' % (c, reponame) for c in r])
        else:
            return ' '.join(['[%s]' % c for c in r])

    def wiki_log(self, reponame):
        """Make wiki text of link to revision log for given repo"""
        if reponame and reponame != '(default)':
            return '[log:%s@%s %s/%s]' % (reponame, ','.join([str(r) for r in
                   self.get_compact()]), _("Revision Log"), reponame)
        else:
            return '[log:@%s %s]' % (','.join([str(r) for r in
                                     self.get_compact()]),
                                     _("Revision Log"))
