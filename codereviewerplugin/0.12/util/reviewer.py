# This is an example implementation of a means to restrict code
# deployments to only changesets whose tickets have been fully
# code reviewed.  This implementation requires that the revision
# table gets populated such as via:
# 
#  [git]
#  cached_repository = true
# 
# If this was previously "false", you may need to resync once:
# 
#  trac-admin /path/to/trac/env repository resync "*"
# 
# An alternative implementation would be where CodeReview included
# a "tickets" column that got populated with the chanegset's tickets
# upon a review record being saved to the db.  You could then search
# the codereviewer table instead of the revision table to map
# changesets to and from tickets.  A benefit of such an approach
# would be an easier means to map back and forth (e.g., no post sql
# query filtering would be needed as it is below) and it would avoid
# known issues with git changeset caching (i.e., not all changesets
# would be seen if using multiple branches apparently).  However, it
# would suffer from not being as complete - e.g., it would not know
# that a ticket's prior changeset was still un-reviewed in PENDING
# if the last changeset PASSED - and so would think the ticket was
# fully reviewed when in fact it wasn't.

import re
import os
import json
import sqlite3
from subprocess import Popen, STDOUT, PIPE, CalledProcessError

from coderev.model import CodeReview


class Env(object):
    def __init__(self, conn):
        self.conn = conn
    def get_db_cnx(self):
        return self.conn

class Reviewer(object):
    """Returns the latest changeset in a given repo whose Trac tickets have
    been fully reviewed.  Works in conjunction with the Trac CodeReviewer
    plugin and its database tables."""
    
    def __init__(self, trac_db, repo_dir, target_ref, data_file,
                 ticket_refs="ref refs"):
        self.trac_db = trac_db
        self.repo_dir = repo_dir
        self.reponame = os.path.basename(repo_dir)
        self.target_ref = target_ref
        self.data_file = data_file
        self.ticket_refs = ticket_refs
    
    def get_next_changeset(self, save=True):
        """Return the next changeset and saves it as the current changeset
        when save is True."""
        current_ref = self.get_current_changeset()
        print "analyzing next changeset after current %s.." % current_ref
        
        # extract changesets in order from current to target ref
        cmds = ['cd %s' % self.repo_dir,
                'git rev-list %s..%s' % (current_ref,self.target_ref)]
        changesets = self._execute(' && '.join(cmds)).splitlines()
        changesets.reverse() # start from current (oldest)
        
        # find last reviewed
        next = current_ref
        for changeset in changesets:
            print "  visiting next changeset %s" % changeset
            if not self.is_reviewed(changeset):
                print "    changeset %s is not reviewed" % changeset
                return self.set_current_changeset(next, save)
            print "    changeset %s is reviewed" % changeset
            next = changeset
        return self.set_current_changeset(next, save)
        
    def is_reviewed(self, changeset):
        """Returns True if all of the given changeset's tickets are fully
        reviewed.  Fully reviewed means that the ticket has no pending
        reviews and the last review has passed."""
        print "analyzing whether changeset %s is reviewed.." % changeset
        
        # extract the commit message from the changeset
        cmds = ['cd %s' % self.repo_dir,
                'git log -1 --pretty="format:%%s" %s' % changeset]
        msg = self._execute(' && '.join(cmds))
        
        # find all tickets referenced in the commit message
        ticket_re = re.compile('#([0-9]+)')
        for ticket in ticket_re.findall(msg):
            if not self._is_fully_reviewed(ticket):
                return False
        return True
    
    def get_current_changeset(self):
        data = self._get_data()
        return data['current']
        
    def set_current_changeset(self, changeset, save=True):
        if save:
            data = self._get_data()
            if data['current'] != changeset:
                data['current'] = changeset
                self._set_data(data)
                print "  setting current changeset to %s" % changeset
            else:
                print "  current changeset already is %s" % changeset
        return changeset
    
    def _get_data(self):
        return json.loads(open(self.data_file,'r').read())
        
    def _set_data(self, data):
        f = open(self.data_file,'w')
        f.write(json.dumps(data))
        f.close()
        
    def _is_fully_reviewed(self, ticket):
        """Returns True if:
        
         * none of the ticket's changesets are PENDING review, -AND-
         * the last changeset is PASSED
        
        Otherwise return False.
        """
        # analyze the review of each ticket's changesets
        for changeset in self._get_ticket_changesets(ticket):
            env = Env(sqlite3.connect(self.trac_db))
            review = CodeReview(env, self.reponame, changeset, 'PENDING')
            
            # are any in pending?
            if review.status == 'PENDING':
                print "  ticket #%s has PENDING reviews" % ticket,
                print "for changeset %s" % review.changeset
                return False
            
        # has last review passed?
        if review.status != "PASSED":
            print "  ticket #%s's last changeset %s = %s (not PASSED)" % \
                    (ticket,changeset,review.status)
            return False
        
        return True
    
    def _get_ticket_changesets(self, ticket):
        """Returns all changesets in chronological/commit order for a
        given ticket.  This implementation requires the revision table
        to be populated using the repository cache."""
        print "  assessing ticket #%s.." % ticket
        changesets = []
        conn = sqlite3.connect(self.trac_db)
        c = conn.cursor()
        c.execute("""
            SELECT rev,message FROM revision
            WHERE message LIKE '%%#%s%%'
            ORDER BY time ASC
            """ % ticket)
        for changeset,msg in c:
            # "ref #1234: fixed" does not reference ticket #123
            ticket_re = re.compile(r'#%s\b' % ticket)
            if ticket_re.search(msg):
                print "    found changeset %s in ticket #%s" % (changeset,ticket)
                changesets.append(changeset)
        return changesets
        
    def _execute(self, cmd):
        p = Popen(cmd, shell=True, stderr=STDOUT, stdout=PIPE)
        out = p.communicate()[0]
        if p.returncode != 0:
            raise Exception('cmd: %s\n%s' % (cmd,out))
        return out
