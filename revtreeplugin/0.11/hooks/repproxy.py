#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2005-2008 Emmanuel Blot
#

import sys

from libsvn import fs, repos, core
from libsvn._core import SubversionException

class RepositoryProxy(object):
    """Simple proxy for the Subversion repository
    """

    # default value
    PATH_MODIFY = fs.svn_fs_path_change_modify
    # path added in txn
    PATH_ADD = fs.svn_fs_path_change_add
    # path removed in txn
    PATH_DELETE = fs.svn_fs_path_change_delete
    # path removed and re-added in txn
    PATH_REPLACE = fs.svn_fs_path_change_replace
    # ignore: internal-use only
    PATH_RESET = fs.svn_fs_path_change_reset

    def __init__(self, repository, transaction=None):
        """Create a new instance of the proxy
        
        If transaction is defined, the proxy is called in a 'pre' commit scripts
        """
        self.pool = core.svn_pool_create(None)
        self.path = repos.svn_repos_find_root_path(repository, self.pool)
        if self.path is None:
            raise Exception, '%s does not appear to be a Subversion ' \
                             'repository.' % repository
        self.repos = repos.svn_repos_open(self.path, self.pool)
        self.fs = repos.svn_repos_fs(self.repos)
        if transaction:
            self.txn = fs.svn_fs_open_txn(self.fs, transaction, self.pool)
        else:
            self.txn = None

    def cleanup(self):
        if self.txn:
            fs.svn_fs_close_txn(self.txn)

    def get_txn_property(self, property):
        if self.txn:
            propval = fs.svn_fs_txn_prop(self.txn, property, self.pool)
            return propval
        else:
            return None

    def set_txn_property(self, property, value):
        if self.txn:
            fs.svn_fs_change_txn_prop(self.txn, property, value, self.pool)
        else:
            raise Exception, "can't use set_txn_property outside pre-commit-hook"

    def get_revision_property(self, revision, property):
        propval = fs.svn_fs_revision_prop(self.fs, revision, property, self.pool)
        return propval

    def set_revision_property(self, revision, property, value):
        fs.svn_fs_change_rev_prop(self.fs, revision, property, value, self.pool)

    def get_revision_properties(self, revision):
        props = fs.svn_fs_revision_proplist(self.fs, revision, self.pool)
        return props

    def get_txn_copy_source(self):
        if not self.txn:
            return None
        root = fs.svn_fs_txn_root(self.txn, self.pool)
        chgpaths = fs.svn_fs_paths_changed(root, self.pool)
        for chgpath in chgpaths:
            (srcrev, srcpath) = fs.svn_fs_copied_from(root, chgpath, self.pool)
            #print >>sys.stderr, "chgpath: %s -> %s @ %d" % (chgpath, srcpath, srcrev)
            if srcrev > 0 and srcpath is not None:
                return (srcrev, srcpath)
        return None

    def get_txn_changed_paths(self):
        if not self.txn:
            return None
        root = self.get_txn_root()
        return self._get_changed_paths(root)

    def get_revision_copy_source(self, revision):
        root = fs.svn_fs_revision_root(self.fs, revision, self.pool)
        chgpaths = fs.svn_fs_paths_changed(root, self.pool)
        for chgpath in chgpaths:
            (srcrev, srcpath) = fs.svn_fs_copied_from(root, chgpath, self.pool)
            #print >>sys.stderr, "chgpath: %s -> %s @ %d" % (chgpath, srcpath, srcrev)
            if srcrev > 0 and srcpath is not None:
                return (srcrev, srcpath)
        return None

    def get_txn_log_message(self):
        if not self.txn:
            return None
        msg = self.get_txn_property('svn:log')
        return msg

    def set_txn_log_message(self, logMsg):
        msg = self.set_txn_property('svn:log', logMsg)

    def get_revision_log_message(self, revision):
        msg = self.get_revision_property(revision, 'svn:log')
        return msg

    def get_txn_author(self):
        if not self.txn:
            return None
        author = self.get_txn_property('svn:author')
        return author
 
    def get_revision_author(self, revision):
        author = self.get_revision_property(revision, 'svn:author')
        return author

    def get_txn_root(self):
        if not self.txn:
            return None
        root = fs.svn_fs_txn_root(self.txn, self.pool)
        return root

    def get_revision_root(self, revision):
        try:
            root = fs.svn_fs_revision_root(self.fs, revision, self.pool)
        except SubversionException:
            return None
        return root

    def get_revision_changed_paths(self, revision):
        root = self.get_revision_root(revision)
        return self._get_changed_paths(root)

    def _get_changed_paths(self, root):
        if not root:
            yield ()
        changes = fs.svn_fs_paths_changed(root, self.pool)
        for (path, desc) in changes.items():
            kind = desc.change_kind
            # FIXME
            # discard the leading slash as the Revtree RE does not expect it
            yield (path[1:], kind)
   
    def get_youngest_revision(self):
        rev = fs.svn_fs_youngest_rev(self.fs, self.pool)
        return rev

    def get_history(self, revision, path, traverse=True):
        """Provides a generator to iterate through the history of a path
          
           revision is the younger revision to start from iterating backwards
           path is the top-level path to search changes from
           traverse should be nulled to stop-on-copy
        """
        history = []
        def history_cb(p, r, pool):
            history.append((r, p))
 
        # svn_repos_history does not support the None argument
        repos.svn_repos_history(self.fs, path, history_cb, 0, revision, \
                                traverse and 1 or 0, self.pool)
        for h in history:
            yield h

    def get_youngest_path_revision(self, path):
        '''This method can be replaced with get_history()'''
        youngest = self.get_youngest_revision()
        length = len(path)
        for rev in range(youngest,0,-1):
            root = self.get_revision_root(rev)
            for (revpath, change) in self.get_revision_changed_paths(rev):
                if revpath[:length] == path:
                    return rev
        return None 

    def find_revision_branch(self, revision, bcre, strict=False):
        '''Find the branch in a changeset.
        revision is the changeset number
        bcre is a compiled regular expression that is used to 
        extract the branch and the path parts from the modified
        repository files/directories 
        if strict is defined, the changeset should only refer to 
        a single directory: the branch; if not defined, the changeset
        should refer to files all located inside the subtree that
        represents the branch'''
        paths = self.get_revision_changed_paths(revision)
        if not strict:
            return self._find_plain_branch(bcre, paths)
        else:
            return self._find_pure_branch(bcre, paths)

    def find_txn_branch(self, bcre, strict=False):
        paths = self.get_txn_changed_paths()
        '''Find the branch in the current transaction.
        bcre is a compiled regular expression that is used to 
        extract the branch and the path parts from the modified
        repository files/directories 
        if strict is defined, the changeset should only refer to 
        a single directory: the branch; if not defined, the changeset
        should refer to files all located inside the subtree that
        represents the branch'''
        if not strict:
            return self._find_plain_branch(bcre, paths)
        else:
            return self._find_pure_branch(bcre, paths)

    def _find_pure_branch(self, bcre, chg_paths):
        change_gen = chg_paths
        item = change_gen.next()
        try:
            change_gen.next()
        except StopIteration:
            pass
        else:
            return None
        (path, change) = item
        # FIXME
        #if kind is not Node.DIRECTORY:
        #    return None
        if change is fs.svn_fs_path_change_add:
            path_mo = bcre.match(path)
        elif change is fs.svn_fs_path_change_delete:
            path_mo = bcre.match(path)
            src_mo = None
        else:
            return None
        if not path_mo:
            return None
        if path_mo.group('path'):
            return None
        # FIXME
        # reinject the leading slash
        return '/%s' % path_mo.group('branch')

    def _find_plain_branch(self, bcre, chg_paths):
        branch = None
        for item in chg_paths:
            (path, change) = item
            mo = bcre.match(path)
            if mo:
                try:
                    br = mo.group('branch')
                except IndexError:
                    raise AssertionError, "Invalid RE: missing 'branch' group"
            else:
                return None
            if not branch:
                branch = br
            elif branch != br:
                raise AssertionError, "'%s' != '%s'" % (br, branch)
        # FIXME
        # reinject the leading slash
        return '/%s' % branch

    def lookup_property(self, revision, path, property): 
        # tests whether the source revision contains the property
        value = self.get_revision_property(revision, property)
        if value:
            # easiest case: the source revision contains the property
            return value
        # complex case: looks up in the branch history for the property
        for rev, path in self.get_history(revision, path):
            value = self.get_revision_property(rev, property)
            if value:
                return value
        # fails to locate the propery
        return None

