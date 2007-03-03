# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2007 Emmanuel Blot <emmanuel.blot@free.fr>
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
import time

from revtree import EmptyRangeError, IRevtreeOptimizer
from trac.versioncontrol import Node, Changeset
from trac.core import *
# only for get_revision_properties
from svn import fs

__all__ = ['Repository']

class BranchChangeset(object):
    """Represents a Subversion revision with additionnal properties"""

    def __init__(self, repos, changeset):
        # Repository
        self.repos = repos
        # Trac changeset
        self.changeset = changeset
        ## revision number
        self.rev = self.changeset.rev
        # branch name
        self.branchname = None
        # clone information (if any)
        self.clone = None
        # last changeset of a branch
        self.last = False
        # SVN properties
        self.properties = None
        
    def __cmp__(self, other):
        """Compares to another changeset, based on the revision number"""
        return cmp(self.rev, other.rev)
            
    def build(self, bcre):
        """Loads a changeset from a SVN repository"""
        """
        cre should define two named groups 'branch' and 'path'
        """
        try:
            if not self._find_simple_branch(bcre):
                self._find_plain_branch(bcre)
        except AssertionError, e:
            raise AssertionError, "%s rev: %d" % (e, self.rev or 0)
        
    def _load_properties(self):
        self.properties = self.repos.get_revision_properties(self.rev)
        
    def prop(self, prop):
        if not isinstance(self.properties, dict):
            self._load_properties()
        return self.properties.has_key(prop) and self.properties[prop] or ''
            
    def props(self, majtype=None):
        if not isinstance(self.properties, dict):
            self._load_properties()
        if majtype is None:
            return self.properties
        else:
            props = {}
            for (k,v) in self.properties.items():
                items = k.split(':')
                if len(items) and (items[0] == majtype):
                    props[items[1]] = v
            return props
            
    def _find_simple_branch(self, bcre):
        change_gen = self.changeset.get_changes()
        item = change_gen.next()
        try:
            change_gen.next()
        except StopIteration:
            pass
        else:
            return False
        (path, kind, change, base_path, base_rev) = item
        if kind is not Node.DIRECTORY:
            return False
        if change is Changeset.COPY:
            path_mo = bcre.match(path)
            src_mo = bcre.match(base_path)
        elif change is Changeset.DELETE:
            self.last = True
            path_mo = bcre.match(base_path)
            src_mo = False
        else:
            return False
        if not path_mo:
            return False
        if path_mo.group('path'):
            return False
        self.branchname = path_mo.group('branch').lower()
        if src_mo:
            self.clone = (int(base_rev), src_mo.group('branch'))
        return True

    def _find_plain_branch(self, bcre):
        branch = None
        for item in self.changeset.get_changes():
            (path, kind, change, base_path, base_rev) = item
            mo = bcre.match(path)
            if mo:
                try:
                    br = mo.group('branch').lower()
                except IndexError:
                    raise AssertionError, "Invalid RE: missing 'branch' group"
            else:
                return False
            if not branch:
                branch = br
            elif branch != br:
                raise AssertionError, 'Incoherent path [%s] != [%s]' \
                                      % (br, branch)
        self.branchname = branch
        return True

class Branch(object):
    """Represents a branch in Subversion, tracking the associated 
       changesets"""

    def __init__(self, name):
        # Name (path)
        self.name = name
        # Source
        self._source = None
        # Changesets instances tied to the branch
        self._changesets = []

    def add_changeset(self, changeset):
        """Adds a new changeset to the branch"""
        self._changesets.append(changeset)
        self._changesets.sort()
        
    def __len__(self):
        """Counts the number of tracked changesets"""
        return len(self._changesets)

    def changesets(self, revrange=None):
        """Returns the tracked changeset as a sequence"""
        if revrange is None:
            return self._changesets
        else:
            return filter(lambda c,mn=revrange[0],mx=revrange[1]: \
                          mn <= c.rev <= mx, self._changesets)

    def revision_range(self):
        """Returns a tuple representing the extent of tracked revisions 
           (first, last)"""
        if not self._changesets:
            return (0, 0)
        return (self._changesets[0].revision, self._changesets[-1].revision)

    def authors(self):
        """Returns a list of authors that have committed to the branch"""
        authors = []
        for chg in self._changesets:
            author = chg.changeset.author
            if author not in authors:
                authors.append(author)
        return authors

    def source(self):
        """Search for the origin of the branch"""
        return self._source

    def youngest(self):
        if len(self._changesets) > 0:
            return self._changesets[-1]
        else: 
            return None

    def oldest(self):
        if len(self._changesets) > 0:
            return self._changesets[0]
        else: 
            return None

    def is_active(self, range):
        y = self.youngest()
        if not y:
            return False
        if not (range[0] <= y.rev <= range[1]):
            return False
        if y.last:
            return False
        return True    

    def build(self, repos):
        if len(self._changesets) > 0:
            clone = self._changesets[0].clone
            if clone:
                node = repos.find_node(clone[1], clone[0])
                self._source = (int(node[1]), node[0])

class Repository(object):
    """Represents a Subversion repositories as a set of branches and a set
       of changesets"""

    def __init__(self, env, authname):
        # Environment
        self.env = env
        # Logger
        self.log = env.log
        # Trac version control
        self._crepos = self.env.get_repository(authname)
        # Dictionnary of changesets
        self._changesets = {}
        # Dictionnary of branches
        self._branches = {}

    def _build_branches(self):
        """Constructs the branch dictionnary from the changeset dictionnary""" 
        for chgset in self._changesets.values():
            br = chgset.branchname
            if not self._branches.has_key(br):
                self._branches[br] = Branch(br)
            self._branches[br].add_changeset(chgset)
        map(lambda b: b.build(self), self._branches.values())

    def changeset(self, revision):
        """Returns a tracked changeset from the revision number"""
        if self._changesets.has_key(revision):
            return self._changesets[revision]
        else:
            return None

    def branch(self, branchname):
        """Returns a tracked branch from its name (path)"""
        if not self._branches.has_key(branchname):
            return None
        else:
            return self._branches[branchname]

    def changesets(self):
        """Returns the dictionnary of changesets (keys are rev. numbers)"""
        return self._changesets

    def branches(self):
        """Returns the dictionnary of branches (keys are branch names)"""
        return self._branches

    def revision_range(self):
        """Returns a tuple representing the extent of tracked revisions 
           (first, last)"""
        return (self._revrange)

    def authors(self):
        """Returns a list of authors that have committed to the repository"""
        authors = []
        for chg in self._changesets.values():
            author = chg.changeset.author
            if author not in authors:
                authors.append(author)
        return authors
        
    def get_revision_properties(self, revision):
        """Returns the revision properties
        Ideally, this should be implemented by Trac core..."""
        return fs.svn_fs_revision_proplist(self._crepos.repos.fs_ptr, revision, 
                                           self._crepos.repos.pool())
                                           
    def find_node(self, path, rev):
        node = self._crepos.get_node(path, rev)
        return (node.get_name(), node.rev)

    def build(self, bcre, revrange=None, timerange=None):
        """Builds an internal representation of the repository, which 
           is used to generate a graphical view of it"""
        start = 0
        stop = int(time.time())
        if timerange:
            if timerange[0]:
                start = timerange[0]
            if timerange[1]:
                stop = timerange[1]
        vcchangesets = self._crepos.get_changesets(start, stop)
        if revrange:
            revmin = self._crepos.get_oldest_rev()
            revmax = self._crepos.get_youngest_rev()
            if revrange[0]:
                revmin = revrange[0]
            if revrange[1]:
                revmax = revrange[1]
            vcsort = [(c.rev, c) for c in vcchangesets \
                      if revmin <= c.rev <= revmax]
        else:
            vcsort = [(c.rev, c) for c in vcchangesets]
        if len(vcsort) < 1:
            raise EmptyRangeError
        vcsort.sort()
        self._revrange = (vcsort[0][1].rev,vcsort[-1][1].rev)
        vcsort.reverse()
        for (rev, vc) in vcsort:
            chgset = BranchChangeset(self, vc)
            chgset.build(bcre)
            self._changesets[rev] = chgset
        self._build_branches()

    def __str__(self):
        """Returns a string representation of the repository"""
        msg = "Revision counter: %d\n" % len(self._changesets)
        for br in self._branches.keys():
            msg += "Branch %s, %d revisions\n" % \
              (br, len(self._branches[br]))
        return msg

