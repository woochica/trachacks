# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Emmanuel Blot <emmanuel.blot@free.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#

import re
import sys
import time
from revtree.repproxy import RepositoryProxy

LOWEST_REV = 160

class Changeset(object):
    """ Represents a changeset, i.e. a Subversion revision with additionnal
        properties """

    # creation reasons of a revision
    NONE, IMPORT, CREATE, BRING, DELIVER, FIX, REF, KILL = range(8)

    def __init__(self):
        # revision number
        self.revision = None
        # log message
        self.log = None
        # date (date as a String)
        self.date = None
        # time (date as seconds elapsed from Epoch)
        self.time = None
        # author
        self.author = None
        # kind of operation
        self.operation = None
        # referenced revision (list)
        self.references = None
        # associated ticket
        self.ticket = None
        # branch name
        self.branchname = None
        # import label
        self.importlabel = None
        # export date
        self.export = None
        # topdir
        self.topdir = ''

    def time(self):
        """ Provides the age of the revision as a count of second 
            since the Epoch """
        if not self.date:
            return None
        core.svn_time_from_cstring(date, self.pool()) / 1000000
            
    def load(self, proxy, revision, topdir, propdomain):
        """ Loads a changeset from a SVN repository """
        self.topdir = topdir
        self.revision = revision
        props = proxy.get_revision_properties(revision)
        for (prop, bufval) in props.items():
            value = str(bufval)
            items = prop.split(':')
            type = items[0].lower()
            if len(items) > 1:
                subtype = items[1].lower()
            else:
                subtype = None
            if type == 'svn':
                self.__setattr__(subtype, value)
                continue
            if type == propdomain:
                if subtype == 'bring':
                    self.operation = Changeset.BRING
                    self.references = [int(value)]
                elif subtype == 'deliver':
                    self.operation = Changeset.DELIVER
                    self.references = [int(r) for r in value.split(',')]
                elif subtype == 'import':
                    if not self.operation:
                        self.operation = Changeset.IMPORT
                        self.importlabel = value
                if subtype == 'export':
                    self.export = value
        action = self.log.split(' ', 1)[0]
        action = action.lower()
        if action in ['fixes', 'closes']:
            self.operation = Changeset.FIX
            #self.ticket = ticket_re.search(self.log)
        elif action == 'refs':
            self.operation = Changeset.REF
            #self.ticket = ticket_re.search(self.log)
        elif action == 'imports':
            self.operation = Changeset.IMPORT
        elif action in ['creates', 'renames']:
            self.operation = Changeset.CREATE
        elif action == 'terminates':
            self.operation = Changeset.KILL
        elif action in ['brings', 'delivers', 'renames']:
            pass
        else:
            raise ValueError, "unsupported message: %s" % self.log
        self.branchname = proxy.find_revision_branch(revision, topdir)
        self.time = proxy.convert_date(self.date)

    def __cmp__(self, other):
        """ Compares to another changeset, based on the revision number """
        return cmp(self.revision, other.revision)


class Branch(object):
    """ Represents a branch in Subversion, tracking the associated 
        changesets """

    def __init__(self, name):
        # Name (path)
        self._name = name
        # Changesets instances tied to the branch
        self._changesets = []

    def add_changeset(self, changeset):
        """ Adds a new changeset to the branch """
        self._changesets.append(changeset)
        self._changesets.sort()

    def __len__(self):
        """ Counts the number of tracked changesets """
        return len(self._changesets)

    def changesets(self):
        """ Returns the tracked changeset as a sequence """
        return self._changesets

    def name(self):
        """ Returns the name (path) of the branch """
        return self._name

    def revision_range(self):
        """ Returns a tuple representing the extent of tracked revisions 
            (first, last) """
        if not self._changesets:
            return (0, 0)
        return (self._changesets[0].revision, self._changesets[-1].revision)

    def authors(self):
        """ Returns a list of authors that have committed to the branch """
        authors = []
        for chg in self._changesets:
            if chg.author not in authors:
                authors.append(chg.author)
        return authors


class Repository(object):
    """ Represents a Subversion repositories as a set of branches and a set
        of changesets """

    def __init__(self, proxy):
        # Repository proxy
        self._proxy = proxy
        # Dictionnary of changesets
        self._changesets = {}
        # Dictionnary of branches
        self._branches = {}
        # Lowset revision number
        self._rev_min = 1
        # Highest revision number
        self._rev_max = self._proxy.get_youngest_revision()

    def _build_branches(self):
        """ Constructs the branch dictionnary from the changeset dictionnary """ 
        for chg in self._changesets.keys():
            rev = int(chg)
            if self._rev_min > rev or not self._rev_min:
                self._rev_min = rev
            if self._rev_max < rev:
                self._rev_max = rev
            br = self._changesets[chg].branchname
            if not self._branches.has_key(br):
                self._branches[br] = Branch(br)
            self._branches[br].add_changeset(self._changesets[chg])

    def changeset(self, revision):
        """ Returns a tracked changeset from the revision number """
        return self._changesets[revision]

    def branch(self, branchname):
        """ Returns a tracked branch from its name (path) """
        return self._branches[branchname]

    def changesets(self):
        """ Returns the dictionnary of changesets (keys are rev. numbers) """
        return self._changesets

    def branches(self):
        """ Returns the dictionnary of branches (keys are branch names) """
        return self._branches

    def revision_range(self):
        """ Returns a tuple representing the extent of tracked revisions 
            (first, last) """
        return (self._rev_min, self._rev_max)

    def authors(self):
        """ Returns a list of authors that have committed to the repository """
        authors = []
        for chg in self._changesets.values():
            if chg.author not in authors:
                authors.append(chg.author)
        return authors
        
    def get_revisions_by_date(self, dayrange):
        """ Returns a tuple of (min, max) revisions from 
            a date range (oldest, newest) """
        current = time.time()
        mintime = current - (dayrange[0]*86400)
        maxtime = current - (dayrange[1]*86400)
        revisions = []
        for chg in self._changesets.values():
            if chg.time < mintime:
                continue
            if chg.time > maxtime:
                continue
            revisions.append(chg.revision)
        revisions.sort()
        if not revisions:
            return (0, 0)
        if len(revisions) >= 2:
            return (revisions[0], revisions[-1])
        return (revisions[0], revisions[0])

    def build(self, topdir, propdomain): 
        head = self._proxy.get_youngest_revision()
        for revision in range(head, LOWEST_REV, -1):
            chgset = Changeset()
            chgset.load(self._proxy, revision, topdir, propdomain)
            self._changesets[chgset.revision] = chgset
        self._build_branches()

    def __str__(self):
        """ Returns a string representation of the repository """
        msg = "Revision counter: %d\n" % len(self._changesets)
        for br in self._branches.keys():
            msg += "Branch %s, %d revisions\n" % \
              (br, len(self._branches[br]))
        return msg

