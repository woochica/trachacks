# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2007 Emmanuel Blot <emmanuel.blot@free.fr>x
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
from datetime import datetime

from revtree import EmptyRangeError, BranchPathError, IRevtreeOptimizer
from trac.core import *
from trac.util.datefmt import utc
from trac.util.text import to_unicode
from trac.versioncontrol import NoSuchNode, Node as TracNode, \
                                Changeset as TracChangeset

__all__ = ['Repository']


class Changeset(object):
    """Represents a Subversion revision with additionnal properties"""

    def __init__(self, repos, changeset):
        # repository
        self.repos = repos
        # environment
        self.env = repos.env
        # trac changeset
        self.changeset = changeset
        # revision number
        self.rev = self.changeset.rev
        # clone information (if any)
        self.clone = None
        # very last changeset of a branch (deleted branch)
        self.last = False
        # SVN properties
        self.properties = None
        
    @staticmethod
    def get_chgset_info(tracchgset):
        chgit = tracchgset.get_changes()
        item = chgit.next()
        info = {}
        try:
            chgit.next()
        except StopIteration:
            info['unique'] = True
        else:
            # more changes are available, i.e. this is not a simple changeset 
            info['unique'] = False
        enum = ('path', 'kind', 'change', 'base_path', 'base_rev')
        for (pos, name) in enumerate(enum):
            info[name] = item[pos]
        return info
    
    def __cmp__(self, other):
        """Compares to another changeset, based on the revision number"""
        return cmp(self.rev, other.rev)
            
    def _load_properties(self):
        if not isinstance(self.properties, dict):
            self.properties = self.repos.get_revision_properties(self.rev)
        
    def prop(self, prop):
        self._load_properties()
        uprop = to_unicode(prop)
        return self.properties.has_key(uprop) and self.properties[uprop] or ''
            
    def props(self, majtype=None):
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


class BranchChangeset(Changeset):
    """Represents a Subversion revision with lies in a regular branch"""
    
    def __init__(self, repos, changeset):
        Changeset.__init__(self, repos, changeset)
        # branch name
        self.branchname = None
        self.prettyname = None

    def _find_simple_branch(self, bcre):
        """A 'simple' changeset is described with a changeset whose only 
           change is a (branch) directory creation or deletion. Neither a file
           nor a subdirectory should be altered in any way
        """
        change_gen = self.changeset.get_changes()
        item = change_gen.next()
        try:
            change_gen.next()
        except StopIteration:
            pass
        else:
            return False
        (path, kind, change, base_path, base_rev) = item
        if kind is not TracNode.DIRECTORY:
            return False
        if change is TracChangeset.COPY:
            path_mo = bcre.match(path)
            src_mo = bcre.match(base_path)
        elif change is TracChangeset.DELETE:
            path_mo = bcre.match(base_path)
            if path_mo and not path_mo.group('path'):
                self.last = True
            src_mo = False
        else:
            return False
        if not path_mo:
            return False
        if path_mo.group('path'):
            return False
        if src_mo:
            self.clone = (int(base_rev), src_mo.group('branch'))
        self.branchname = path_mo.group('branch')
        mo_dict = path_mo.groupdict()
        self.prettyname = 'branchname' in mo_dict and mo_dict['branchname'] \
                            or self.branchname
        return True

    def _find_plain_branch(self, bcre):
        """A 'plain' changeset is a regular changeset, with file addition, 
           deletion or modification
        """
        branch = None
        for item in self.changeset.get_changes():
            (path, kind, change, base_path, base_rev) = item
            mo = bcre.match(path)
            if mo:
                try:
                    br = mo.group('branch')
                except IndexError:
                    raise AssertionError, "Invalid RE: missing 'branch' group"
            else:
                return False
            if not branch:
                branch = br
            elif branch != br:
                raise BranchPathError, "'%s' != '%s'" % (br, branch)
        self.branchname = branch
        mo_dict = mo.groupdict()
        self.prettyname = 'branchname' in mo_dict and mo_dict['branchname'] \
                            or self.branchname
        return True

    def build(self, bcre):
        """Loads a changeset from a SVN repository
        bcre should define two named groups 'branch' and 'path'
        """
        try:
            if self._find_simple_branch(bcre):
                return True
            if self._find_plain_branch(bcre):
                return True
        except BranchPathError, e:
            self.env.log.warn("%s @ rev %s" % (e, self.rev or 0))
        return True


class TagChangeset(Changeset):
    """Represent a Subversion 'tags' which is barely not more than a regular
       changeset tied to a specific directory
    """
    
    def __init__(self, repos, changeset):
        Changeset.__init__(self, repos, changeset)
        self.repos = repos
        self.name =  None
        self.prettyname = None

    def _find_tagged_changeset(self, bcre):
        info = self.get_chgset_info(self.changeset)
        if not info:
            return False
        if not info['unique']:
            self.env.log.warn('Tag: too complex')
            return False
        if info['kind'] is not TracNode.DIRECTORY:
            self.env.log.warn('Tag: not a dir: %s: %s' % \
                                (info['kind'], info['path']))
            return False
        path_mo = bcre.match(info['path'])
        if info['change'] is TracChangeset.DELETE:
            mo_dict = path_mo.groupdict()
            if 'tag' not in mo_dict:
                return False
            self.name = mo_dict['tag']
            self.env.log.info('Tag: deleted %s' % info['path'])
            self.last = True
            return True 
        if info['change'] is not TracChangeset.COPY:
            self.env.log.warn('Tag: not a copy: %s: %s' % \
                                (info['change'], info['path']))
            return False
        if not path_mo: # or not src_mo:
            self.env.log.warn('Tag: with path: %s <- %s' % \
                                (info['path'], info['base_path']))
            return False
        if path_mo.group('path'):
            self.env.log.warn('Tag: cannot have path')
            return False
        try:
            node = self.repos.get_node(info['path'], self.changeset.rev)
        except NoSuchNode:
            return False
        (prev_path, prev_rev, prev_chg) = node.get_previous()
        self.env.log.info("PREV: %s %s %s" % (prev_path, prev_rev, prev_chg))
        self.clone = (int(prev_rev), prev_path)
        mo_dict = path_mo.groupdict()
        if 'tag' not in mo_dict:
            return False
        self.name = mo_dict['tag']
        self.prettyname = mo_dict.setdefault('tagname', self.name)
        return True

    def build(self, bcre):
        return self._find_tagged_changeset(bcre)
            
    def source(self):
        return self.clone and self.repos.changeset(self.clone[0])


class Branch(object):
    """Represents a branch in Subversion, tracking the associated 
       changesets"""

    def __init__(self, name, prettyname):
        # Name (path)
        self.name = name
        self.prettyname = prettyname
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
        # Dictionary of changesets
        self._changesets = {}
        # Dictionary of branches
        self._branches = {}
        # Dictionary of tags
        self._tags = {}

    def _dispatch(self):
        """Constructs the branch and tag dictionaries from the changeset 
           dictionary""" 
        for chgset in self._changesets.values():
            if isinstance(chgset, BranchChangeset):
                br = chgset.branchname
                if not self._branches.has_key(br):
                    self._branches[br] = Branch(br, chgset.prettyname)
                self._branches[br].add_changeset(chgset)
            elif isinstance(chgset, TagChangeset):
                if self._tags.has_key(chgset.name):
                    if chgset.last:
                        self.log.info('Removing deleted tag %s' % chgset.name)
                        del self._tags[chgset.name]
                        continue
                    self.log.warn('Ubiquitous tag: %s', chgset.name)
                self._tags[chgset.name] = chgset 
        map(lambda b: b.build(self), self._branches.values())

    def changeset(self, revision):
        """Returns a tracked changeset from the revision number"""
        if self._changesets.has_key(revision):
            return self._changesets[revision]
        else:
            return None

    def branch(self, branchname):
        """Returns a tracked branch from its name (path)
           
           branchname should be a unicode string, and should not start with
           a leading path separator (/)
        """
        if not self._branches.has_key(branchname):
            return None
        else:
            return self._branches[branchname]

    def changesets(self):
        """Returns the dictionary of changesets (keys are rev. numbers)"""
        return self._changesets

    def branches(self):
        """Returns the dictionary of branches (keys are branch names)"""
        return self._branches
        
    def tags(self):
        """Returns the dictionary of tags (keys are tag names)"""
        return self._tags

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
        """Returns the revision properties"""
        changeset = self._crepos.get_changeset(revision)
        return changeset.get_properties()
        
    def get_node_properties(self, path, revision):
        return self._crepos.get_node(path, revision).get_properties()
        
    def get_node(self, path, revision):
        return self._crepos.get_node(path, revision)
                                           
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
        dtstart = datetime.fromtimestamp(start, utc)
        dtstop = datetime.fromtimestamp(stop, utc)
        vcchangesets = self._crepos.get_changesets(dtstart, dtstop)
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
            info = Changeset.get_chgset_info(vc)
            chgset = None
            mo = info and bcre.match(info['path'])
            if mo:
                mo_dict = mo.groupdict()
                if 'branch' in mo_dict and mo_dict['branch']:
                    chgset = BranchChangeset(self, vc)
                if 'tag' in mo_dict and mo_dict['tag']:
                    chgset = TagChangeset(self, vc)
            if chgset and chgset.build(bcre):
                self._changesets[rev] = chgset
            else:
                self.log.warn('Changeset neither a known branch or tag: %s' % 
                              (info or vc))
        self._dispatch()

    def __str__(self):
        """Returns a string representation of the repository"""
        msg = "Revision counter: %d\n" % len(self._changesets)
        for br in self._branches.keys():
            msg += "Branch %s, %d revisions\n" % \
              (br, len(self._branches[br]))
        return msg

