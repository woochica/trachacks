
# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2005 Edgewall Software
# Copyright (C) 2005 Tressieres Thomas <thomas.tressieres@free.fr>
# All rights reserved.
#
# This software may be used and distributed according to the terms
# of the GNU General Public License, incorporated herein by reference.
#
# Author: Thomas Tressières <thomas.tressieres@free.fr>
#         based on work of Jason Parks <jparks@jparks.net>


from __future__ import generators

import os
import time
import posixpath
import re

from trac.util import TracError, shorten_line, escape, FALSE
from trac.versioncontrol import Changeset, Node, Repository, IRepositoryConnector
from trac.versioncontrol.web_ui import ChangesetModule, BrowserModule
from trac.wiki import IWikiSyntaxProvider
from trac.core import *

try:
    import p4
    has_perforce = True
except ImportError:
    has_perforce = False
    ui = object
    pass


### Version Control API


TmpFileName = os.tempnam() + "_perforce_output.bin"

def _normalize_path(path):
    """
    Return a canonical representation of path in the repos.
    """
    return path + "..."

def _add_rev_to_path(path, rev):
    """
    Add revision to path.
    """
    if rev == None:
        cmd = path + '#head'
    else:
        cmd = path + '@' + rev
    return cmd



class PerforceStream(object):
    """
    Wrapper object
    """

    def __init__(self, content):
        self.content = content
        self.pos = 0

    def read(self, amt=None):
        if amt == None:
            return self.content[:amt]
        self.pos += int(amt)
        return self.content[self.pos-int(amt):self.pos]



class PerforceRepository(Repository):
    """
    Repository implementation for perforce
    """
    p4c = 0
    p4init = 0

    def __init__(self, name, log, options):
        #log.debug("*** __init__ repository (is init: %d)" % (self.__class__.p4init))
        Repository.__init__(self, name, None, log)
        if self.__class__.p4init == 0:
            self.__class__.p4init = 1
            self.__class__.p4c = p4.P4()
            self.__class__.p4c.port = options['port']
            self.__class__.p4c.user = options['user']
            self.__class__.p4c.client = options['client']
            self.__class__.p4c.password = options['passwd']
            self.__class__.p4c.parse_forms()
            try:
                self.__class__.p4c.connect()
            except self.__class__.p4c.P4Error:
                for e in p4.errors:
                    self.log.debug(e)
                self.__class__.p4init = 0

        try:
            # cache the first few changes
            self.history = []
            changes = self.__class__.p4c.run("changes", "-m", "options['max_changes']", "-s", "submitted")
            for change in changes:
                self.history.append(change['change'])

        except self.__class__.p4c.P4Error:
            for e in p4.errors:
                self.log.debug(e)
            self.__class__.p4init = 0


    def close(self):
        """
        Close the connection to the repository.
        """
        raise NotImplementedError


    def get_changeset(self, rev):
        """
        Retrieve a Changeset object that describes the changes made in revision 'rev'.
        """
        #self.log.debug("*** get_changeset rev = %s" % (rev))
        change = { }
        try:
            if rev != None:
                change = self.__class__.p4c.run_describe(str(rev))[0]
            else:
                young = self.get_youngest_rev()
                change = self.__class__.p4c.run_describe(str(young))[0]
        except self.__class__.p4c.P4Error:
            for e in p4.errors:
                self.log.debug(e)
        return PerforceChangeset(self.__class__.p4c, rev, change, self.log)


    def has_node(self, path, rev):
        """
        Tell if there's a node at the specified (path,rev) combination.
        """
        #self.log.debug("*** has_node %s   %s" % (path, rev))
        try:
            self.get_node()
            return True
        except TracError:
            return False


    def get_node(self, path, rev=None):
        """
        Retrieve a Node (directory or file) from the repository at the
        given path. If the rev parameter is specified, the version of the
        node at that revision is returned, otherwise the latest version
        of the node is returned.
        """
        #self.log.debug("*** get_node path = '%s' rev = %s" % (path, rev))
        if path != '/':
            if path.startswith("//") == False:
                path = path.rstrip('/')
                path = '/' + path

            if path.endswith("...") == True:
                path2 = path.rstrip('...')
                dir = self.__class__.p4c.run("dirs", path2)
            else:
                #path = "\"" + path + "\""
                dir = self.__class__.p4c.run("dirs", path)

            if len(dir) != 0:
                kind = Node.DIRECTORY
            else:
                kind = Node.FILE
        else:
            kind = Node.DIRECTORY
        return PerforceNode(path, rev, self.__class__.p4c, self.log, kind)


    def get_oldest_rev(self):
        #self.log.debug("*** get_oldest_rev rev = %s" % (self.history[-1]))
        return self.history[-1]


    def get_youngest_rev(self):
        """
        Return the youngest revision in the repository.
        """
        rev = self.__class__.p4c.run("changes", "-m", "1", "-s", "submitted")[0]['change']
        #self.log.debug("*** get_youngest_rev rev = %s" % (rev))

        if rev != self.history[0]:
            count = int(rev) - int(self.history[0])
            changes = self.__class__.p4c.run("changes", "-m", count, "-s", "submitted")
            idx = 0
            for change in changes:
                num = change['change']
                if rev != num:
                    #self.log.debug("*** inserting change %s into history at %d" % (num, idx))
                    self.history.insert(idx, num)
                    idx += 1
                else:
                    break
        return rev


    def previous_rev(self, rev):
        """
        Return the revision immediately preceding the specified revision.
        """
        #self.log.debug("*** previous_rev rev = %s" % (rev))
        idx = self.history.index(rev)
        if idx + 1 < len(self.history):
            return self.history[idx + 1]
        return None


    def next_rev(self, rev):
        """
        Return the revision immediately following the specified revision.
        """
        #self.log.debug("*** next_rev rev = %s" % (rev))
        idx = self.history.index(rev)
        if idx > 0:
            return self.history[idx - 1]
        return None


    def rev_older_than(self, rev1, rev2):
        """
        Return True if rev1 is older than rev2, i.e. if rev1 comes before rev2
        in the revision sequence.
        """
        #self.log.debug("rev_older_than =  %s %s" % (rev1, rev2))
        raise NotImplementedError


    def get_path_history(self, path, rev=None, limit=None):
        """
        Retrieve all the revisions containing this path (no newer than 'rev').
        The result format should be the same as the one of Node.get_history()
        """
        #self.log.debug("get_path_history =  %s %s %s" % (path, rev, limit))
        raise NotImplementedError


    def normalize_path(self, path):
        """
        Return a canonical representation of path in the repos.
        """
        #self.log.debug("normalize_path =  %s" % (path))
        if path != '/':
            if path.endswith("/...") == True:
                return path
            if path.startswith("//") == False:
                path = path.rstrip('/')
                path = '/' + path
            dir = self.__class__.p4c.run("dirs", path)
            if len(dir) != 0:
                kind = Node.DIRECTORY
            else:
                kind = Node.FILE
        else:
            kind = Node.DIRECTORY
        #if kind == Node.DIRECTORY:
        #    return path + "/..."
        return path


    def normalize_rev(self, rev):
        """
        Return a canonical representation of a revision in the repos.
        'None' is a valid revision value and represents the youngest revision.
        """
        if rev == None:
            rev = self.get_youngest_rev()
        elif int(rev) > int(self.get_youngest_rev()):
            raise TracError, "Revision %s doesn't exist yet" % rev
        #self.log.debug("normalize_rev =  %s" % (rev))
        return rev
        



class PerforceNode(Node):
    """
    Represents a directory or file in the repository.
    """
    def __init__(self, path, rev, p4c, log, kind):
        self.p4c = p4c
        self.log = log

        Node.__init__(self, path, rev, kind)

        if self.isfile:
            self.content = None
            self.info = self.p4c.run("files", path)[0]


    def _get_content(self):
        cmd = _add_rev_to_path(self.path, self.rev)

        #self.log.debug("*** content =  %s" % (cmd))
        type = self.p4c.run("fstat", cmd)
        if type[0]['headType'].startswith('binary') == True or type[0]['headType'].startswith('ubinary') == True:
            file = self.p4c.run("print", "-o", TmpFileName, cmd)
            f = open(TmpFileName, 'rb')
            self.content = f.read()
            f.close()
        else:
            file = self.p4c.run("print", cmd)
            del file[0]
            sep = '\n'
            self.content = sep.join(file)
        ##self.log.debug("*** content =  %s" % (self.content))
        return self.content


    def get_content(self):
        """
        Return a stream for reading the content of the node. This method
        will return None for directories. The returned object should provide
        a read([len]) function.
        """
        if self.isdir:
            return None
        return PerforceStream(self._get_content()) 


    def get_entries(self):
        """
        Generator that yields the immediate child entries of a directory, in no
        particular order. If the node is a file, this method returns None.
        """
        #self.log.debug("*** get_entries for '%s' %s kind = %s" % (self.path, self.rev, self.kind))
        if self.isfile:
            return
        path = _add_rev_to_path(self.path + "/*", self.rev)
        dirs = self.p4c.run("dirs", path)
        #self.log.debug("---    dirs = '%s'" % (dirs))

        for dir in dirs:
            mydir = _add_rev_to_path(dir['dir'] + "...", self.rev)
            changes = self.p4c.run("changes", "-m 1 -status submitted", mydir)
            maxrev = str(changes[0]["change"])

            yield PerforceNode(dir['dir'], maxrev, self.p4c, self.log, Node.DIRECTORY)

        if self.path != '/':
            files = self.p4c.run("files", path)
            for file in files:
                #self.log.debug("found file '%s'" % (file['depotFile']))
                change = self.p4c.run("fstat", _add_rev_to_path(file['depotFile'], self.rev))[0]
                rev = change['headChange']
                if change['headAction'] != 'delete':
                    yield PerforceNode(file['depotFile'], rev, self.p4c, self.log, Node.FILE)


    def get_history(self, limit=None):
        """
        Generator that yields (path, rev, chg) tuples, one for each revision in which
        the node was changed. This generator will follow copies and moves of a
        node (if the underlying version control system supports that), which
        will be indicated by the first element of the tuple (i.e. the path)
        changing.
        Starts with an entry for the current revision.
        """
        histories = []

        cmd = _add_rev_to_path(_normalize_path(self.path), self.rev)
        #self.log.debug("*** get_history = %s  %s" % (cmd, limit))
        if self.isfile:
            logs = self.p4c.run("filelog", "-m", str(limit), cmd)
            #self.log.debug("*** get_history logs %s" % (logs))
            index = 0
            while index < len(logs[0]['rev']):
                chg = Changeset.EDIT
                path = self.path
                rev = logs[0]['change'][index]
                action = logs[0]['action'][index]
    
                if action == 'add':
                    chg = Changeset.ADD
                elif action == 'integrate':
                    chg = Changeset.COPY
                elif action == 'branch':
                    chg = Changeset.COPY
                    histories.append([path, rev, chg])
                    path = logs[0]['file'][index][0]
                    chg = Changeset.EDIT
                    rev = str(int(rev) - 1)
                elif action == 'delete':
                    chg = Changeset.DELETE
                
                histories.append([path, rev, chg])
                index += 1
        else:
            logs = self.p4c.run("changes", "-s", "submitted", "-L", "-m", str(limit), cmd)
            #self.log.debug("*** get_history logs %s %s %s" % (self.path, logs, cmd))
            _index = 0
            for myLog in logs:
                histories.append([self.path, myLog['change'], Changeset.EDIT])
                _index += 1

        for c in histories:
            yield tuple(c)


    def get_properties(self):
        """
        Returns a dictionary containing the properties (meta-data) of the node.
        The set of properties depends on the version control system.
        """
        #self.log.debug("*** get_properties = %s rev=%s" % (self.path, self.rev))
        return { }


    def get_content_length(self):
        if self.isdir:
            return None
        type = self.p4c.run("fstat", "-Ol", self.path)
        if type[0]['headAction'].startswith('delete') == True:
            return 0
        #self.log.debug("*** get_content_length = %s %d" % (type, int(type[0]['fileSize'])) )
        return int(type[0]['fileSize'])


    def get_content_type(self):
        #self.log.debug("*** get_content_type = %s  rev = %s" % (self.path, self.rev))
        if self.isdir:
            return None
        change = self.p4c.run("fstat", self.path)[0]
        if change['headType'].startswith('binary') == True or change['headType'].startswith('ubinary') == True:
            return 'application/octet-stream'
        return None


    def get_last_modified(self):
        #self.log.debug("*** get_last_modified = %s" % self.path)
        return int(self.info['time'])



class PerforceChangeset(Changeset):
    """
    Represents a set of changes of a repository.
    """

    def __init__(self, p4c, rev, change, log):
        self.log = log
        self.rev = rev
        self.change = change
        self.p4c = p4c
        message = ""
        author = ""
        date = 0
        #self.log.debug("*** changeset init = %s  rev = %s" % (change, rev))
        if len(change) != 0: 
            message = self.change['desc']	
            author = self.change['user']
            date = int(self.change['time'])
        Changeset.__init__(self, rev, message, author, date)

    def get_changes(self):
        """
        Generator that produces a (path, kind, change, base_path, base_rev)
        tuple for every change in the changeset, where change can be one of
        Changeset.ADD, Changeset.COPY, Changeset.DELETE, Changeset.EDIT or
        Changeset.MOVE, and kind is one of Node.FILE or Node.DIRECTORY.
        """
        #self.log.debug("*** get_changes = %s" % (self.change))
        files = self.change['depotFile']
        changes = []
        
        index = 0
        for file in files:
            #rev = self.change['rev'][index]
            rev = str(int(self.rev) - 1)
            action = self.change['action'][index]
            #self.log.debug("*** get_changes %s %s %s" % (file, action, rev))

            if action == 'integrate':
                filelog = self.p4c.run("filelog", "-m", "1", file)
                action = Changeset.COPY
                changes.append([file, Node.FILE, action, filelog[0]['file'][0][0], rev])
            else:
                changes.append([file, Node.FILE, action, file, rev])
            index += 1

        for c in changes:
            yield tuple(c)



### Components

class PerforceConnector(Component):

    implements(IRepositoryConnector)

    def identifiers(self):
        """Support the `p4:` and `perforce:` schemes"""
        global has_perforce
        if has_perforce:
            yield ("perforce", 8)
            yield ("p4", 8)

    def repository(self, type, dir, authname):
        """Return a `PerforceRepository`"""
        options = {}
        for key, val in self.config.options(type):
            options[key] = val
        #self.log.debug("*** type = %s, options = %s" % (type, options))

        return PerforceRepository(dir, self.log, options)


class PerforceBrowserModule(BrowserModule):

    # IRequestHandler methods

    def process_request(self, req):
        # before:
        #branch = req.args.get('branch')
        #tag = req.args.get('tag')
        #if branch:
        #    req.args['rev'] = branch
        #elif tag:
        #    req.args['rev'] = tag
        return BrowserModule.process_request(self, req)

    def _render_file(self, req, repos, node, rev=None):
        BrowserModule._render_file(self, req, repos, node, rev)
        # after:
        #self._add_tags_and_branches(req, repos, rev)

    def _render_directory(self, req, repos, node, rev=None):
        BrowserModule._render_directory(self, req, repos, node, rev)
        # after:
        #self._add_tags_and_branches(req, repos, rev)

    def _add_tags_and_branches(self, req, repos, rev):
        # TODO: consider pushing that in BrowserModule.process_request and
        #       extend the API with Repository.get_tags and Repository.get_branches 
        tags = []
        for t, rev in repos.get_tags():
            tags.append({'name': escape(t), 'rev': rev})
        branches = []
        for b, rev in repos.get_branches():
            branches.append({'name': escape(b), 'rev': rev})
        req.hdf['browser.tags'] = tags
        req.hdf['browser.branches'] = branches


class PerforceChangesetModule(ChangesetModule):

    # IRequestHandler methods

    def match_request(self, req):
        # accept any form of revision, including tag names
        match = re.match(r'/changeset/([\w\-+./:]+)$', req.path_info)
        if match:
            req.args['rev'] = match.group(1)
            return 1

    def _render_html(self, req, repos, chgset, diff_options):
        ChangesetModule._render_html(self, req, repos, chgset, diff_options)
        # plus:
        #properties = []
        #hg = PerforceConnector(self.env)
        #for name, value, htmlclass in chgset.properties():
        #    if htmlclass == 'changeset':
        #        value = ' '.join([hg.format_changeset(v, v) for v in \
        #                          value.split()])
        #    properties.append({'name': name,
        #                       'value': value,
        #                       'htmlclass': htmlclass})
        #req.hdf['changeset.properties'] = properties


### Helpers 
        
#class trac_ui(ui):
#    def __init__(self):
#        ui.__init__(self, interactive=False)
#        
#    def write(self, *args): pass
#    def write_err(self, str): pass

#    def readline(self):
#        raise TracError('*** Perforce ui.readline called ***')                                                             
        
