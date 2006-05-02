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

import sys

from libsvn import fs, repos, core
from libsvn._core import SubversionException

class RepositoryProxy(object):
    """ Proxy for the Subversion repository """

    # The following value should be defined in libsvn !
    SVN_FS_PATH_CHANGE_MODIFY, \
    SVN_FS_PATH_CHANGE_ADD, \
    SVN_FS_PATH_CHANGE_DELETE, \
    SVN_FS_PATH_CHANGE_REPLACE, \
    SVN_FS_PATH_CHANGE_RESET = range(5)

    def __init__(self, repository, transaction=None):
        if isinstance(repository, unicode): 
 		    repository = repository.encode('utf-8') 
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
        propval = fs.svn_fs_txn_prop(self.txn, property, self.pool)
        return propval

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
            if srcrev > 0 and srcpath is not None:
                return (srcrev, srcpath)
        return None

    def get_revision_copy_source(self, revision):
        root = fs.svn_fs_revision_root(self.fs, revision, self.pool)
        chgpaths = fs.svn_fs_paths_changed(root, self.pool)
        for chgpath in chgpaths:
            (srcrev, srcpath) = fs.svn_fs_copied_from(root, chgpath, self.pool)
            print >>sys.stderr, "chgpath: %s -> %s @ %d" % (chgpath, srcpath, srcrev)
            if srcrev > 0 and srcpath is not None:
                return (srcrev, srcpath)
        return None

    def get_txn_log_message(self):
        if not self.txn:
            return None
        msg = self.get_txn_property('svn:log')
        return msg

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

    def get_txn_changed_paths(self):
        if not self.txn:
            return None
        root = self.get_txn_root()
        return self._get_changed_paths(root)

    def _get_changed_paths(self, root):
        if not root:
            return []
        paths = fs.svn_fs_paths_changed(root, self.pool)
        return paths
   
    def get_youngest_revision(self):
        rev = fs.svn_fs_youngest_rev(self.fs, self.pool)
        return rev

    def get_history(self, revision, path):
        history = []
        def history_cb(p, r, pool):
            history.append((r, p))

        repos.svn_repos_history(self.fs, path, history_cb, 0, revision, 1, self.pool)
        for h in history:
            yield h

    def get_youngest_path_revision(self, path):
        '''This method can be replaced with get_history()'''
        youngest = self.get_youngest_revision()
        length = len(path)
        for rev in range(youngest,0,-1):
            root = self.get_revision_root(rev)
            revpaths = self.get_revision_changed_paths(rev)
            if not revpaths:
                return None
            for revpath in revpaths.keys():
                if revpath[:length] == path:
                    return rev
        return None 

    def find_revision_branch(self, revision, directory, strict=False):
        paths = self.get_revision_changed_paths(revision)
        path = self._find_moved_branch(revision, paths)
        if path:
            return path
        try:
            return self._find_branch(paths, directory, strict)
        except AssertionError, e:
            raise AssertionError, "%s rev: %d paths %s" % (e, revision, paths)

    def find_txn_branch(self, directory, strict=False):
        paths = self.get_txn_changed_paths()
        return self._find_branch(paths, directory, strict)
        
    def convert_date(self, date):
        return core.svn_time_from_cstring(date, self.pool) / 1000000

    def _find_moved_branch(self, revision, paths):
        pathnames = paths.keys()
        if len(pathnames) != 2:
            return None
        srcpath = None
        dstpath = None
        for path in pathnames:
            kind = paths[path].change_kind 
            if kind == RepositoryProxy.SVN_FS_PATH_CHANGE_DELETE:
                srcpath = path
            elif kind == RepositoryProxy.SVN_FS_PATH_CHANGE_ADD:
                dstpath = path
            else:
                return None
        if not srcpath or not dstpath:
            return None
        root = fs.svn_fs_revision_root(self.fs, revision, self.pool)
        (srev, spath) = fs.svn_fs_copied_from(root, dstpath, self.pool)
        if spath and spath == srcpath:
            return dstpath
        return None

    def _find_branch(self, paths, directory, strict):
        branch = None
        for path in paths.keys():
            pos = path.find(directory)
            if pos != -1:
                br = path[:pos].lower()
            else:
                if strict:
                    return None
                br = path.lower()
            if not branch:
                branch = br.lower()
            elif branch != br:
                brlen = min(len(branch), len(br))
                if branch[:brlen] != br[:brlen]:
                    raise AssertionError, 'Incoherent path (%s,%s)' \
                                      % (br, branch)
                else:
                  branch = branch[:brlen]
        return branch

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

