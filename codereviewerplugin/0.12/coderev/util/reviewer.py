import re
import os
import json
import sqlite3
from subprocess import Popen, STDOUT, PIPE

from coderev.model import CodeReview
from trac.env import Environment
from trac.ticket.model import Ticket
from trac.resource import ResourceNotFound

class Reviewer(object):
    """Returns the latest changeset in a given repo whose Trac tickets have
    been fully reviewed.  Works in conjunction with the Trac CodeReviewer
    plugin and its database tables."""
    
    def __init__(self, trac_env, repo_dir, target_ref, data_file, verbose=True):
        self.env = Environment(trac_env)
        self.repo_dir = repo_dir.rstrip('/')
        self.reponame = os.path.basename(self.repo_dir).lower()
        self.target_ref = target_ref
        self.data_file = data_file
        self.verbose = verbose
    
    def get_next_changeset(self, save=True):
        """Return the next reviewed changeset and save it as the current
        changeset when save is True."""
        next = self.get_current_changeset()
        for changeset in self.get_changesets():
            if self.verbose:
                print '.',
            if not self.is_complete(changeset):
                return self.set_current_changeset(next, save)
            next = changeset
        return self.set_current_changeset(next, save)
    
    def get_blocking_changeset(self):
        """Return the next blocking changeset."""
        # find last *not* reviewed
        for changeset in self.get_changesets():
            if not self.is_complete(changeset):
                return changeset
        return None
    
    def get_blocked_tickets(self):
        """Return all tickets of blocking changesets in order of them
        getting unblocked."""
        tickets = []
        visited = set([])
        found = False
        changesets = self.get_changesets()
        for changeset in changesets:
            if not found and self.is_complete(changeset):
                changesets.pop(0)
                continue
            
            review = self.get_review(changeset)
            if not found:
                # all changesets must come after the blocking one
                blocking_when = review.changeset_when
            
            found = True
            for ticket in review.tickets:
                if ticket not in visited:
                    visited.add(ticket)
            
                    def get_first_remaining_changeset():
                        for review in self.get_reviews(ticket):
                            if review.changeset in changesets and \
                               review.changeset_when >= blocking_when:
                                return review # changeset exists on path
                        raise ResourceNotFound()
                    
                    # the ticket's oldest *remaining* changeset determines blockage
                    # i.e., if current is already past a changeset, do not consider it
                    try:
                        first = get_first_remaining_changeset()
                        tkt = Ticket(self.env, ticket)
                        tkt.first_changeset = first.changeset
                        tkt.first_changeset_when = first.changeset_when
                        tickets.append( tkt )
                    except ResourceNotFound:
                        pass # e.g., incorrect ticket reference
        return sorted(tickets, key=lambda t: t.first_changeset_when)
    
    def get_changesets(self):
        """Extract changesets in order from current to target ref."""
        current_ref = self.get_current_changeset()
        review = self.get_review(current_ref)
        when = int(review.changeset_when / CodeReview.EPOCH_MULTIPLIER)
        cmds = ['cd %s' % self.repo_dir,
                'git rev-list --reverse --no-merges --since=%s HEAD' % when]
        changesets = self._execute(' && '.join(cmds)).splitlines()
        if self.verbose:
            print "\n%d changesets from current %s to target %s" % \
                    (len(changesets),current_ref,self.target_ref)
        return changesets
    
    def get_reviews(self, ticket):
        return CodeReview.get_reviews(self.env, ticket)
    
    def get_review(self, changeset):
        return CodeReview(self.env, self.reponame, changeset)
    
    def is_complete(self, changeset):
        """Returns True if all of the given changeset's tickets are complete.
        Complete means that the ticket has no pending reviews and the last
        review has passed, -AND- the ticket's completeness criteria (if any)
        is satisfied."""
        review = self.get_review(changeset)
        for ticket in review.tickets:
            reason = review.is_incomplete(ticket)
            if reason:
                if self.verbose:
                    print '\n' + reason
                return False
        return True
    
    def _execute(self, cmd):
        p = Popen(cmd, shell=True, stderr=STDOUT, stdout=PIPE)
        out = p.communicate()[0]
        if p.returncode != 0:
            raise Exception('cmd: %s\n%s' % (cmd,out))
        return out
    
    def get_current_changeset(self):
        data = self._get_data()
        return data['current']
    
    def set_current_changeset(self, changeset, save=True):
        if save:
            data = self._get_data()
            if data['current'] != changeset:
                data['current'] = changeset
                self._set_data(data)
                if self.verbose:
                    print "setting current changeset to %s" % changeset
            elif self.verbose:
                print "current changeset already is %s" % changeset
        return changeset
    
    def _get_data(self):
        if os.path.exists(self.data_file):
            data = json.loads(open(self.data_file,'r').read())
        else:
            # grab the latest rev as the changeset
            cmds = ['cd %s' % self.repo_dir,
                    'git log -1 --pretty="format:%H"']
            changeset = self._execute(' && '.join(cmds))
            data = {'current': changeset}
            self._set_data(data)
        return data
    
    def _set_data(self, data):
        f = open(self.data_file,'w')
        f.write(json.dumps(data))
        f.close()
