import re
import os
import json
import sqlite3
from subprocess import Popen, STDOUT, PIPE

from coderev.model import CodeReview
from trac.env import Environment

class Reviewer(object):
    """Returns the latest changeset in a given repo whose Trac tickets have
    been fully reviewed.  Works in conjunction with the Trac CodeReviewer
    plugin and its database tables."""
    
    def __init__(self, trac_env, repo_dir, target_ref, data_file):
        self.env = Environment(trac_env)
        self.repo_dir = repo_dir.rstrip('/')
        self.reponame = os.path.basename(repo_dir)
        self.target_ref = target_ref
        self.data_file = data_file
    
    def get_next_changeset(self, save=True):
        """Return the next changeset and saves it as the current changeset
        when save is True."""
        current_ref = self.get_current_changeset()
        
        # extract changesets in order from current to target ref
        cmds = ['cd %s' % self.repo_dir,
                'git rev-list --reverse %s..%s' % (current_ref,self.target_ref)]
        changesets = self._execute(' && '.join(cmds)).splitlines()
        print "\n%d changesets from current %s to target %s" % \
                (len(changesets),current_ref,self.target_ref)
        
        # find last reviewed
        next = current_ref
        for changeset in changesets:
            print '.',
            if not self.is_reviewed(changeset):
                return self.set_current_changeset(next, save)
            next = changeset
        return self.set_current_changeset(next, save)
        
    def is_reviewed(self, changeset):
        """Returns True if all of the given changeset's tickets are fully
        reviewed.  Fully reviewed means that the ticket has no pending
        reviews and the last review has passed."""
        review = CodeReview(self.env, self.reponame, changeset)
        for ticket in review.tickets:
            if not self._is_fully_reviewed(ticket):
                return False
        return True
        
    def _is_fully_reviewed(self, ticket):
        """Returns True if:
        
         * none of the ticket's changesets are PENDING review, -AND-
         * the last changeset is PASSED
        
        Otherwise return False.
        """
        # analyze the review of each ticket's changesets
        for review in CodeReview.get_reviews(self.env, ticket):
            # are any in pending?
            if review.status == 'PENDING':
                print "\nticket #%s has PENDING reviews" % ticket,
                print "for changeset %s" % review.changeset
                return False
            
        # has last review passed?
        if review.status != "PASSED":
            print "\nticket #%s's last changeset %s = %s (not PASSED)" % \
                    (ticket,review.changeset,review.status)
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
                print "setting current changeset to %s" % changeset
            else:
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
        return data
    
    def _set_data(self, data):
        f = open(self.data_file,'w')
        f.write(json.dumps(data))
        f.close()
