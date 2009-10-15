# -*- coding: utf-8 -*-
#
# Authors: Lewis Baker <lewbaker99@hotmail.com>
#          Thomas Tressières <thomas.tressieres@free.fr>

"""Perforce repository classes that can be used to query information
about Perforce entities.
"""

import re
import protocols
from perforce.results import IOutputConsumer
from p4trac.util import AutoAttributesMeta

# FIXME: 
# This is a hack around the fact that a Connection object with empty client
# will default to the user name client and you can not add new attributes to a
# Connection object. We use a dummy client name to indicate that we don't want
# to use the client
NO_CLIENT = '_P4TRAC_DUMMY_CLIENT'


class _P4ChangeInfo(object):
    """A data structure for recording info about a changelist.

    @ivar change: The changelist number.
    @ivar user: The username of the user that created the changelist.
    @ivar description: The change description.
    @ivar time: The unix time the change was submitted.
    @ivar client: The name of the client the change was submitted from.
    @ivar files: A list of the file paths modified in this changelist.
    """

    __slots__ = [
        'change', 'user', 'description', 'time', 'client', 'status', 'files'
        ]

    def __init__(self, change):
        self.change = int(change)
        self.user = None
        self.description = None
        self.time = None
        self.client = None
        self.status = None
        self.files = None


class _P4FileInfo(object):
    """A data structure for recording info about a file.

    @ivar path: The repository path in depot notation.
    @ivar rev: The file revision number.
    @ivar action: The action that was performed on this revision.
    @ivar change: The changelist number this revision belongs to.
    @ivar type: The file type of this revision.
    @ivar sources: List of (nodePath, how) tuples identifying other files that
    were integrated into this revision. how is one of 'branch', 'copy',
    'ignore', 'merge', 'edit', 'delete'.
    @ivar attributes: Dictionary of key/value pairs of file attributes.
    """

    __slots__ = [
        'path', 'rev', 'action', 'change', 'type', 'size', 'sources',
        'attributes'
        ]

    def __init__(self, path, rev=None, change=None):
        self.path = path
        self.rev = rev
        self.change = change
        self.type = None
        self.action = None
        self.size = None
        self.sources = None
        self.attributes = None


class _P4DirectoryInfo(object):
    """A data structure for recording info about a directory.

    @ivar path: The repository path in depot notation (no trailing slash)
    @ivar subdirs: A list of the names of subdirectories in this directory
    @ivar files: A list of the names of files in this directory
    @ivar change: The number of the most recent changelist that affected files
    under this directory.
    """

    __slots__ = [
        'path', 'subdirs', 'files', 'change',
        ]

    def __init__(self, path):
        self.path = path
        self.subdirs = None
        self.files = None
        self.change = None


class PerforceError(Exception):
    def __init__(self, errors):
        self.errors = errors

    def __str__(self):
        return '\n'.join([e.format() for e in self.errors])


class NoSuchChangelist(Exception):
    def __init__(self, change):
        self.change = change


class NoSuchNode(Exception):
    def __init__(self, path, rev):
        self.path = path
        self.rev = rev


class NoSuchFile(NoSuchNode):
    pass


class NoSuchDirectory(NoSuchNode):
    pass

# Some regular expressions used by P4NodePath
_slashDotSlashRE = re.compile(ur'/(\./)+')
_dirSlashDotDotRE = re.compile(ur'[^/]+/..(/|$)')
_trailingSlashesRE = re.compile(ur'(?<=[^/])/*$')

class P4NodePath(object):
    """A path to a node in the Perforce repository.

    A node is a particular revision of a path in the Perforce repository and
    may be either a file, directory or non-existant.
    """

    __metaclass__ = AutoAttributesMeta

    __slots__ = ['_path', '_rev']

    @staticmethod
    def normalisePath(path):
        """Normalise the Perforce repository path.

        * Collapses 'dir/..', '/./', './' and '/.'.
        * Removes trailing slashes.
        * Adds leading '//'.
        * Returns the same object unmodified if already normalised.
         
        @param path: The Perforce repository path to normalise. C{str} paths
        are assumed to be C{unicode} strings encoded using the UTF-8 encoding.
        @type path: C{unicode}, C{str} or C{None}

        @return: A string representing the normalised path.
        @rtype: C{unicode} or C{None}
        """

        if path is None:
            return None
        else:
            from p4trac.util import toUnicode
            path = toUnicode(path)

        # Collapse any '/./' to '/'
        if path.find(u'/./') != -1:
            path = _slashDotSlashRE.sub(u'/', path)

        # Remove any leading './'
        if path.startswith(u'./'):
            path = path[2:]

        # Remove any trailing '/.'
        if path.endswith(u'/.'):
            path = path[:-2]

        # Collapse any 'dir/..' to ''
        # Need to iterate here to handle 'a/b/../..' collapsing to ''
        while path.find(u'/..') > 0:
            path, count = _dirSlashDotDotRE.subn(u'', path)
            if not count:
                break

        if not path:
            return None
        
        if not path.startswith(u'//') or path.startswith(u'///'):
            path = u'//%s' % path.lstrip(u'/')

        if path == u'//':
            return path
        
        # Remove any trailing slashes
        if path.endswith(u'/'):
            path = _trailingSlashesRE.sub(u'', path)
        
        return path

    @staticmethod
    def normaliseRevision(rev):
        """Normalise the Perforce revision specifier.

        Returns a unicode string representing the Perforce revision.
        """
        if rev is None:
            return None

        from p4trac.util import toUnicode
        rev = toUnicode(rev)

        if not rev:
            return None
        
        elif rev.startswith(u'#'):
            # A file revision
            return rev

        elif rev.startswith(u'@'):
            # A repository revision
            return rev

        else:
            # Assume it's a repository revision (change number, label,
            # date or client) that needs a leading '@' added.
            return u'@%s' % rev

    def __init__(self, path, rev=None):
        """Construct a P4NodePath object.

        @param path: The depot path to the node.
        This must be a normalised path. Call L{P4NodePath.normalisePath} if
        normalisation is required.
        @type path: C{unicode}

        @param rev: The revision of the node or C{None} for the head revision.
        Any revision not starting with '@' or '#' will be assumed to have an
        implicit leading '@'.
        @type rev: C{int}, C{str}, C{unicode}, C{None}
        """
        assert isinstance(path, unicode)
        self._path = path
        self._rev = P4NodePath.normaliseRevision(rev)

    def _get_path(self):
        """The depot path of the node in the Perforce repository.

        @type: C{unicode}
        """
        return self._path

    def _get_rev(self):
        """The revision of the node in the Perforce repository.

        If C{None} then the latest revision is implied.

        @type path: C{unicode} or C{None}
        """
        return self._rev

    def _get_fullPath(self):
        """The full path to the node including the revision if one is
        specified.

        @type: C{unicode}
        """
        if self.rev is None:
            return self.path
        else:
            return u'%s%s' % (self.path, self.rev)

    def _get_leaf(self):
        """The final component of the path.

        The part after the last slash (the file name for file paths and the
        directory name for directory paths).

        Has the value C{u''} if this is the root path.

        @type: C{unicode}

        @see: L{parent}
        """
        i = self.path.rfind(u'/')
        if i == -1:
            return u''
        else:
            return self.path[i+1:]
        
    def _get_parent(self):
        """The parent directory of this node path.

        This is the part before the last slash or C{u'//'} if this path is a
        depot path of form C{u'//depot'}.

        @type: C{unicode}
        """
        i = self.path.rfind(u'/', 2)
        if i == -1:
            return u'//'
        else:
            return self.path[:i]

    def _get_isRoot(self):
        """Boolean flag indicating if this path is the root path (C{u'//'})
        or not.
        
        @type: C{boolean}
        """
        return self.path == u'//'

    def _get_isRepositoryRevision(self):
        """Boolean flag indicating if the revision specifier is a repository
        revision or not.
        
        Repository revisions start with the C{u'@'} character.
        
        @note: The C{None} revision is considered a repository revision as
        well as a file revision.
        
        @type: C{boolean}
        """
        return self.rev is None or self.rev.startswith(u'@')

    def _get_isFileRevision(self):
        """Boolean flag indicating if the revision specifier is a file revision
        or not.
        
        File revisions start with the C{u'#'} character.
        
        @note: The C{None} revision is considered a repository revision as
        well as a file revision.
        
        @type: C{boolean}
        """
        return self.rev is None or self.rev.startswith(u'#')

    def _get_change(self):
        """The change number for a change repository revision.
        
        Has the value C{None} if the revision isn't a change revision.
        
        @type: C{int} or C{None}
        """
        if self.rev is not None and self.rev.startswith(u'@'):
            try:
                return int(self.rev[1:])
            except ValueError:
                return None
        else:
            return None

    def __str__(self):
        return self.fullPath.encode('utf8')

    def __unicode__(self):
        return self.fullPath

    def __hash__(self):
        return hash(self.path) ^ hash(self.rev)

    def __eq__(self, other):
        if isinstance(other, P4NodePath):
            return self.path == other.path and self.rev == other.rev
        else:
            return False

    def __ne__(self, other):
        return not (self == other)


class _P4Changelist(object):
    """A proxy object that gives access to details about a particular
    changelist in a Perforce repository.

    It lazily evaluates requests for information by executing Perforce
    commands.
    """

    __metaclass__ = AutoAttributesMeta

    __slots__ = ['_repo', '_change']

    def __init__(self, change, repository):
        """Construct a new _P4Changelist object.

        @param change: The change number of the changelist to query.
        @type change: C{int}

        @param repository: The Perforce repository the changelist belongs to.
        @type repository: L{Repository}
        """
        self._change = int(change)
        self._repo = repository

    def _get_user(self):
        """The user that created this changelist.

        @type: C{unicode}

        @raise NoSuchChangelist: If the changelist doesn't exist in the
        Perforce repository.
        """
        info = self._repo._getChangeInfo(self._change)
        if info is None or info.user is None:
            try:
                self._repo._runDescribe([self._change])
            except PerforceError:
                raise NoSuchChangelist(self._change)
            info = self._repo._getChangeInfo(self._change)
        return info.user

    def _get_description(self):
        """The description associated with this changelist.

        @type: C{unicode}

        @raise NoSuchChangelist: If the changelist doesn't exist in the
        Perforce repository.
        """
        info = self._repo._getChangeInfo(self._change)
        if info is None or info.description is None:
            try:
                self._repo._runDescribe([self._change])
            except PerforceError:
                raise NoSuchChangelist(self._change)
            info = self._repo._getChangeInfo(self._change)
        return info.description

    def _get_time(self):
        """The time the change was last updated or submitted.

        @type: C{int}

        @raise NoSuchChangelist: If the changelist doesn't exist in the
        Perforce repository.
        """
        info = self._repo._getChangeInfo(self._change)
        if info is None or info.time is None:
            try:
                self._repo._runDescribe([self._change])
            except PerforceError:
                raise NoSuchChangelist(self._change)
            info = self._repo._getChangeInfo(self._change)
        return info.time

    def _get_client(self):
        """The name of the client the changelist was submitted from.

        @type: C{unicode}

        @raise NoSuchChangelist: If the changelist doesn't exist in the
        Perforce repository.
        """
        info = self._repo._getChangeInfo(self._change)
        if info is None or info.client is None:
            try:
                self._repo._runDescribe([self._change])
            except PerforceError:
                raise NoSuchChangelist(self._change)
            info = self._repo._getChangeInfo(self._change)
        return info.client

    def _get_status(self):
        """The status of the changelist.

        Either C{u'submitted'} or C{u'pending'}.

        @type: C{unicode}

        @raise NoSuchChangelist: If the changelist doesn't exist in the
        Perforce repository.
        """
        info = self._repo._getChangeInfo(self._change)
        if info is None or info.status is None:
            try:
                self._repo._runDescribe([self._change])
            except PerforceError:
                raise NoSuchChangelist(self._change)
            info = self._repo._getChangeInfo(self._change)
        return info.status

    def _get_nodes(self):
        """A list of the nodes affected by this changelist.

        Has the value None if the changelist is not submitted.

        @type: C{list} of L{_P4Node} objects or C{None}

        @raise NoSuchChangelist: If the changelist doesn't exist in the
        Perforce repository.
        """

        if self.status != u'submitted':
            return None

        info = self._repo._getChangeInfo(self._change)
        assert info is not None

        if info.files is None:
            self._repo._runDescribe([self._change])
            
        assert info.files is not None

        nodes = []
        for path in info.files:
            nodePath = P4NodePath(path, self._change)
            node = _P4Node(nodePath, self._repo)
            nodes.append(node)
        return nodes


class _P4Node(object):
    """A Perforce node is a particular revision of a path in the repository.
    """

    __metaclass__ = AutoAttributesMeta

    __slots__ = ['_repo', '_nodePath']

    def __init__(self, nodePath, repository):
        self._nodePath = nodePath
        self._repo = repository

    def _get_nodePath(self):
        """The node path of this node.

        @type: L{P4NodePath}
        """
        return self._nodePath

    def _get_isDirectory(self):
        """Boolean flag indicating whether the L{_P4Node} is a directory.

        @type: C{boolean}
        """

        # The root path is always a directory
        if self._nodePath.isRoot:
            return True

        # Use the latest revision if no revision specified
        if self._nodePath.rev is None:
            latestChange = self._repo.getLatestChange()
            self._nodePath = P4NodePath(self._nodePath.path, latestChange)

        # Do we already know it's a directory?
        dirInfo = self._repo._getDirInfo(self._nodePath)
        if dirInfo is not None:
            return True

        # Do we already know it's a file?
        fileInfo = self._repo._getFileInfo(self._nodePath)
        if fileInfo is not None:
            if fileInfo.action != u'delete':
                return False

        # Check if it is a directory
        try:
            self._repo._runDirs(self._nodePath)
        except PerforceError:
            return False

        dirInfo = self._repo._getDirInfo(self._nodePath)
        return dirInfo is not None

    def _get_isFile(self):
        """Boolean flag indicating whether the L{_P4Node} is a file.

        @type: C{boolean}
        """

        # The root path is always a directory
        if self._nodePath.isRoot:
            return False

        # Use the latest revision if no revision specified
        if self._nodePath.rev is None:
            latestChange = self._repo.getLatestChange()
            self._nodePath = P4NodePath(self._nodePath.path, latestChange)

        # Do we already know it's a file?
        fileInfo = self._repo._getFileInfo(self._nodePath)
        if fileInfo is not None and fileInfo.action is not None:
            if fileInfo.action == u'delete':
                return False
            else:
                return True

        # Do we already know it's a directory?
        dirInfo = self._repo._getDirInfo(self._nodePath)
        if dirInfo is not None:
            return False

        # Check if it is a file
        try:
            self._repo._runFstat(self._nodePath)
        except PerforceError:
            return False

        fileInfo = self._repo._getFileInfo(self._nodePath)
        if fileInfo is not None:
            if fileInfo.action == u'delete':
                return False
            else:
                return True
        else:
            return False

    def _get_exists(self):
        """Boolean flag indicating whether the L{_P4Node} exists or not.

        @type: C{boolean}

        @see: L{isFile}, L{isDirectory}
        """
        return self.isFile or self.isDirectory

    def _get_fileRevision(self):
        """Integer value indicating the file revision of this node.

        @type: C{int}

        @raise NoSuchFile: If the L{_P4Node} isn't a file.
        """

        if not self.isFile:
            fileInfo = self._repo._getFileInfo(self._nodePath)
            if fileInfo is None:
                raise NoSuchFile(self._nodePath.path,
                                 self._nodePath.rev)
        else:
            fileInfo = self._repo._getFileInfo(self._nodePath)
            
        assert fileInfo is not None

        return fileInfo.rev    

    def _get_fileSize(self):
        """The size in bytes of this file node.

        @type: C{int}

        @raise NoSuchFile: If the L{_P4Node} isn't a file node.
        """

        if not self.isFile:
            raise NoSuchFile(self._nodePath.path,
                             self._nodePath.rev)

        fileInfo = self._repo._getFileInfo(self._nodePath)
        assert fileInfo is not None

        if fileInfo.size is None:
            self._repo._runFstat(self._nodePath)
        assert fileInfo.size is not None

        return fileInfo.size

    def _get_fileContent(self):
        """A file-like object that gives access to the contents of the
        file.

        @type: C{file}-like object

        @raise NoSuchFile: If the L{_P4Node} isn't a file.
        """

        if not self.isFile:
            raise NoSuchFile(self._nodePath.path,
                             self._nodePath.rev)

        from p4trac.util import FastTemporaryFile
        tempFile = FastTemporaryFile()
        output = _P4PrintOutputConsumer(tempFile)
        self._repo._connection.run(
            'print',
            self._repo.fromUnicode(self._nodePath.fullPath),
            output=output)
        if output.errors:
            raise PerforceError(output.errors)

        tempFile.seek(0)
        return tempFile

    def _get_change(self):
        """The change number of the most recent change to this node.

        @type: C{int}

        @raise NoSuchNode: If the L{_P4Node} doesn't exist.
        """

        # Use the latest revision if no revision specified
        if self._nodePath.rev is None:
            latestChange = self._repo.getLatestChange()
            self._nodePath = P4NodePath(self._nodePath.path, latestChange)

        if not self.exists:
            fileInfo = self._repo._getFileInfo(self._nodePath)
            if fileInfo is None:
                raise NoSuchNode(self._nodePath.path,
                                 self._nodePath.rev)
            else:
                return fileInfo.change

        if self.isFile:
            # Report the most recent change for the file
            fileInfo = self._repo._getFileInfo(self._nodePath)
            assert fileInfo is not None
            assert fileInfo.change is not None
            return fileInfo.change

        else:
            # Report the most recent change for any files under the directory
            dirInfo = self._repo._getDirInfo(self._nodePath, create=True)
            if self._nodePath.path == u'//':
                self._repo._log.debug('   _get_change getDirInfo %d' % (self._nodePath.change))
                return self._nodePath.change
            if dirInfo is None or dirInfo.change is None:
                self._repo._runChanges(self._nodePath,
                                       maxChanges=1,
                                       wildcard=u'...')
                dirInfo = self._repo._getDirInfo(self._nodePath)
            assert dirInfo.change is not None
            return dirInfo.change

    def _get_action(self):
        """The most recent action performed on this file node.

        One of 'add', 'edit', 'delete', 'branch', 'import', 'integrate'.

        @raise NoSuchFile: If this node is not a file node.
        """

        if self.isFile:
            fileInfo = self._repo._getFileInfo(self._nodePath)
            assert fileInfo is not None
        else:
            # It may not be a file because it's deleted
            fileInfo = self._repo._getFileInfo(self._nodePath)
            if fileInfo is None:
                raise NoSuchFile(self._nodePath.path,
                                 self._nodePath.rev)

        assert fileInfo.action is not None
        return fileInfo.action

    def _get_type(self):
        """The Perforce file type for this file node.

        @type: C{unicode}

        @raise NoSuchFile: If this node is not a file node.
        """

        if not self.isFile:
            raise NoSuchFile(self._nodePath.path,
                             self._nodePath.rev)

        fileInfo = self._repo._getFileInfo(self._nodePath)
        assert fileInfo is not None
        assert fileInfo.type is not None

        return fileInfo.type

    def _get_attributes(self):
        """The set of attributes for this file node.

        @type: C{dict} of C{unicode} to C{unicode}
        """

        if not self.isFile:
            raise NoSuchFile(self._nodePath.path,
                             self._nodePath.rev)

        fileInfo = self._repo._getFileInfo(self._nodePath)
        assert fileInfo is not None

        if fileInfo.attributes is None:
            try:
                self._repo._runFstat(self._nodePath)
            except PerforceError:
                return False
            
        return fileInfo.attributes
    
    def _get_integrations(self):
        """The set of files that were integrated into this file revision.

        @type: A list of (nodePath, how) pairs that identifies the files that
        were integrated and how each of those files were integraded. 'how' is
        one of 'branch', 'copy', 'merge', 'ignore', 'edit' or 'delete'.

        @raise NoSuchFile: If this node is not a file node.
        """

        if not self.isFile:
            raise NoSuchFile(self._nodePath.path,
                             self._nodePath.rev)

        fileInfo = self._repo._getFileInfo(self._nodePath)
        assert fileInfo is not None

        if fileInfo.sources is None:
            self._repo._runFileLog(self._nodePath)

        return fileInfo.sources
    
    def _get_subDirectories(self):
        """A list of subdirectory nodes of this directory.

        @raise NoSuchDirectory: If this node is not a directory node.
        """

        if not self.isDirectory:
            raise NoSuchDirectory(self._nodePath.path,
                                  self._nodePath.rev)

        dirInfo = self._repo._getDirInfo(self._nodePath, create=True)
        if dirInfo.subdirs is None:
            self._repo._runDirs(self._nodePath, subdirs=True)

        assert dirInfo.subdirs is not None

        subdirNodes = []
        for subdir in dirInfo.subdirs:
            if self._nodePath.isRoot:
                if self._repo._connection.client != NO_CLIENT:
                    nodePath = P4NodePath(u'//%s/%s' % (self._repo._connection.client, subdir),
                                          self._nodePath.rev)
                else:
                    nodePath = P4NodePath(u'//%s' % subdir,
                                          self._nodePath.rev)
            else:
                nodePath = P4NodePath(u'%s/%s' % (self._nodePath.path, subdir),
                                      self._nodePath.rev)

            self._repo._log.debug("_P4Node._get_subDirectories '%s'" % (nodePath._path))
            node = _P4Node(nodePath, self._repo)
            subdirNodes.append(node)
        return subdirNodes

    def _get_files(self):
        """A list of file nodes in this directory.

        @raise NoSuchDirectory: If this node is not a directory node.
        """

        if not self.isDirectory:
            raise NoSuchDirectory(self._nodePath.path, self._nodePath.rev)

        # The root path never has any files under it
        if self._nodePath.isRoot:
            return []

        dirInfo = self._repo._getDirInfo(self._nodePath, create=True)
        if dirInfo.files is None:
            try:
                self._repo._runFstat(self._nodePath, wildcard=u'*')
            except PerforceError:
                if dirInfo.files is None:
                    raise
        assert dirInfo.files is not None

        fileNodes = []
        for file in dirInfo.files:
            nodePath = P4NodePath(u'%s/%s' % (self._nodePath.path, file),
                                  self._nodePath.rev)
            node = _P4Node(nodePath, self._repo)
            fileNodes.append(node)
        return fileNodes


class P4Repository(object):
    """The repository object.

    The root of all Perforce repository queries.

    Maintains a cache of information retrieved so far so that info isn't
    retrieved more than once.
    """

    def __init__(self, connection, log):
        """Create a new Perforce repository object.

        Associated with a Perforce server via a connection that it uses to
        query information about the repository.

        The connection must already be connected.
        """

        self._log = log
        self._connection = connection
        assert self._connection.connected

        from perforce import CharSet
        cs = CharSet(self._connection.charset)
        if cs is CharSet.UTF_8:
            self._codec = 'utf8'
        elif cs is CharSet.NOCONV:
            self._codec = 'iso8859_1'
        else:
            raise NotImplementedError("Charset '%s' not supported" % str(cs))

        self._latestChange = None

        # Mapping from change number (int) to _P4ChangeInfo object
        self._changes = {}

        # Mapping from node-path (unicode) to _P4DirectoryInfo object
        self._dirs = {}

        # Mapping from node-path (unicode) to _P4FileInfo object
        self._files = {}

        self._serverVersion = None

    def toUnicode(self, string):
        """Convert a string to a unicode string if it isn't already."""
        from p4trac.util import toUnicode
        return toUnicode(string, self._codec)

    def fromUnicode(self, string):
        """Convert a string from a unicode string to a string suitable for
        passing to the perforce run() command.
        """
        if self._codec != 'utf8':
            return string.encode(self._codec)
        else:
            return string

    def getServerVersion(self):
        if self._serverVersion is None:
            if self._connection.server == '0':
                # Need to run a command first
                self._connection.run('info')
            self._serverVersion = int(self._connection.server)
        return self._serverVersion

    def getChangelist(self, change):
        """Get the _P4Changelist object corresponding to the change number."""
        return _P4Changelist(change, self)

    def isChangelistCached(self, change):
        """Query if info on a particular changelist is cached."""
        info = self._changes.get(change, None)
        if info is None:
            return False
        else:
            return (info.user is not None and
                    info.description is not None and
                    info.description is not None and
                    info.time is not None)

    def getLatestChange(self):
        """Return the number of the most recently submitted change.

        Returns 0 if no changes have been submitted.
        """
        if self._latestChange is None:
            output = P4ChangesOutputConsumer(self)
            self._connection.run('changes',
                                 '-m', '1',
                                 '-l',
                                 '-s', 'submitted',
                                 output=output)
            if output.changes:
                self._latestChange = output.changes[0]
            elif not output.errors:
                self._latestChange = 0
            else:
                raise PerforceError(output.errors)
        return self._latestChange

    def getNextChange(self, change):
        """Return the number of the next change submitted after change.

        Returns None if no changes have been submitted after this one.
        """

        assert change >= 0

        if self._latestChange is not None and change >= self._latestChange:
            return None
        
        # What is the next highest change that we already know about?
        higherKnownChanges = [c
                              for c in self._changes.iterkeys()
                              if c > change]
        if higherKnownChanges:
            nextLowestKnownChange = min(higherKnownChanges)
        else:
            if self.getLatestChange() <= change:
                return None
            else:
                nextLowestKnownChange = self.getLatestChange()

        assert nextLowestKnownChange > change

        if nextLowestKnownChange == change + 1:
            return nextLowestKnownChange

        # We perform a bounded linear search on the set of change numbers
        # between change and nextLowestKnownChange. Don't use a binary search
        # here as we are searching over all submitted changes which shouldn't
        # have too big a gap (unlike searching for the next change for a
        # particular node which could have arbitrary sized gaps).

        batchSize = 50      # Randomly chosen batch size for performance
        lowerBound = change + 1
        upperBound = nextLowestKnownChange

        while lowerBound <= upperBound:

            batchUpperBound = lowerBound + batchSize

            output = P4ChangesOutputConsumer(self)
            self._connection.run('changes', '-l', '-s', 'submitted',
                                 '-m', str(batchSize),
                                 '@>=%i,@<=%i' % (lowerBound,
                                                  batchUpperBound),
                                 output=output)

            if output.errors:
                raise PerforceError(output.errors)

            if output.changes:
                lowest = min(output.changes)
                assert lowest >= lowerBound
                assert lowest <= batchUpperBound

                # We know there are no earlier changes
                return lowest
            else:
                # There are no changes between lowerBound and batchUpperBound
                # We need to try searching higher.
                lowerBound = batchUpperBound + 1

        # Didn't find the next change (it doesn't exist)
        return None
            
    def getNode(self, nodePath):
        """Get the _P4Node object corresponding to the node path.

        nodePath is a P4NodePath object
        """
        return _P4Node(nodePath, self)

    def precacheFileInformationForChanges(self, changes):
        """Pre-caches integration and change information for the file
        revisions affected by the specified list of changes.

        Information that has already been retrieved is not requeried.
        """

        changesToDescribe = []
        for change in changes:
            changeInfo = self._getChangeInfo(change)
            if changeInfo is None or changeInfo.files is None:
                changesToDescribe.append(change)

        # Describe the changes in batches of 1000
        for i in xrange(0, len(changesToDescribe), 1000):
            changesBatch = changesToDescribe[i:i+1000]

            output = _P4DescribeOutputConsumer(self)
            self._connection.run('describe', '-s',
                                 output=output,
                                 *[str(int(c)) for c in changesBatch])

            if output.errors:
                raise PerforcError(output.errors)

        def filesWithoutCachedHistory():
            for change in changes:
                changeInfo = self._getChangeInfo(change)
                assert changeInfo is not None
                assert changeInfo.files is not None
                
                for file in changeInfo.files:
                    nodePath = P4NodePath(file, '@%i' % change)
                    fileInfo = self._getFileInfo(nodePath)
                    assert fileInfo is not None

                    if fileInfo.sources is None:
                        yield nodePath

        def batchesOfFilesWithoutCachedHistory(batchSize):
            batch = []
            for file in filesWithoutCachedHistory():
                batch.append(file)
                if len(batch) == batchSize:
                    yield batch
                    batch = []
            if batch:
                yield batch

        for batch in batchesOfFilesWithoutCachedHistory(1000):
            output = _P4FileLogOutputConsumer(self)
            self._connection.run('filelog', '-m', '1',
                                 output=output,
                                 *[self.fromUnicode(np.fullPath)
                                   for np in batch])
            if output.errors:
                raise PerforceError(output.errors)

    def clearFileInformationCache(self):
        """Clear any cached file information.

        You can call this method to clear cached data about file information
        to save memory if you know that you aren't going to need the cached
        file information again.
        """
        self._changes = {}
        self._dirs = {}
        self._files = {}

    def _getChangeInfo(self, change, create=False):
        """Get the changelist info structure for the specified change number.

        @param change: The change number to query.
        @type change: C{int}

        @param create: Boolean flag indicating whether to force creation of
        the change info data structure if it doesn't already exist. Pass
        C{True} for this parameter if you know that the specified change
        number exists.
        @type create: C{boolean}

        @return: The changelist info structure or C{None} if the change
        doesn't yet exist in the cache.
        @rtype: L{_P4ChangeInfo} or C{None}
        """

        if change in self._changes:
            return self._changes[change]
        elif create:
            info = _P4ChangeInfo(int(change))
            self._changes[change] = info
            return info
        else:
            return None

    def _getDirInfo(self, nodePaths, create=False):
        """Get the directory info structure for the set of nodePaths.

        @param nodePaths: Either a P4NodePath or a list of P4NodePath objects.
        If a list is provided, then you must already know that all of the
        NodePaths refer to the same _P4Node (this implies that the path component
        of the NodePaths are all equal).

        @param create: If true and the nodePaths aren't already in existence
        then a new empty _P4DirectoryInfo object is inserted into the database
        and is returned, otherwise None is returned. Should only be set to
        True if you already know that the nodePaths are a directory.

        @return: The L{_P4DirectoryInfo} object for the nodePaths or C{None},
        @rtype: L{_P4DirectoryInfo} or C{None}
        """

        if isinstance(nodePaths, list):
            # A list of equivalent node paths
            for nodePath in nodePaths:
                assert nodePath.rev is not None
                assert nodePath.path == nodePaths[0].path

            fullPaths = [np.fullPath for np in nodePaths]

            # Get any existing info elements in the database
            infos = [self._dirs[p]
                     for p in fullPaths
                     if p in self._dirs]

            if infos:
                # There are existing info objects, pick the first one
                # and merge in any details from the others
                info = infos[0]
                for other in infos[1:]:
                    if other is not info:
                        assert other.path == info.path

                        if other.subdirs is not None:
                            if info.subdirs is None:
                                info.subdirs = other.subdirs
                            else:
                                assert info.subdirs == other.subdirs

                        if other.files is not None:
                            if info.files is None:
                                info.files = other.files
                            else:
                                assert info.files == other.files

                        if other.change is not None:
                            if info.change is None:
                                info.change = other.change
                            else:
                                assert info.change == other.change

                # Update all node paths to point to the same info
                for p in fullPaths:
                    self._dirs[p] = info
                return info
            elif create and nodePaths:
                info = _P4DirectoryInfo(nodePaths[0].path)
                for p in fullPaths:
                    self._dirs[p] = info
                return info
            else:
                return None
        else:
            # A single node path
            nodePath = nodePaths
            assert nodePath.rev is not None

            fullPath = nodePath.fullPath
            if fullPath in self._dirs:
                return self._dirs[fullPath]
            elif create:
                info = _P4DirectoryInfo(nodePath.path)
                self._dirs[fullPath] = info
                return info
            else:
                return None

    def _getFileInfo(self, nodePaths, create=False):
        """Get the file info structure for the set of nodePaths.

        @param nodePaths: Either a P4NodePath or a list of P4NodePath objects.
        If a list is provided, then you must already know that all of the
        NodePaths refer to the same _P4Node (this implies that the path
        component of the NodePaths are all equal).

        @param create: If true and the nodePaths aren't already in existence
        then a new _P4FileInfo object is inserted into the database and is
        returned, otherwise None is returned. Should only be set to True if
        you already know the nodePaths are a file.
        """

        if isinstance(nodePaths, list):
            # A list of equivalent node paths
            for nodePath in nodePaths:
                assert nodePath.rev is not None
                assert nodePath.path == nodePaths[0].path

            fullPaths = [np.fullPath for np in nodePaths]

            # Get any existing info elements in the database
            infos = [self._files[p]
                     for p in fullPaths
                     if p in self._files]
            if infos:
                # There are existing info objects, pick the first one
                # and merge in any details from the others
                info = infos[0]
                for other in infos[1:]:
                    if other is not info:
                        assert other.path == info.path

                        if other.rev is not None:
                            if info.rev is None:
                                info.rev = other.rev
                            else:
                                assert info.rev == other.rev

                        if other.action is not None:
                            if info.action is None:
                                info.action = other.action
                            else:
                                assert info.action == other.action

                        if other.change is not None:
                            if info.change is None:
                                info.change = other.change
                            else:
                                assert info.change == other.change

                        if other.type is not None:
                            if info.type is None:
                                info.type = other.type
                            else:
                                assert info.type == other.type

                        if other.size is not None:
                            if info.size is None:
                                info.size = other.size
                            else:
                                assert info.size == other.size

                        if other.sources is not None:
                            if info.sources is None:
                                info.sources = other.sources
                            else:
                                assert info.sources == other.sources

                        if other.attributes is not None:
                            if info.attributes is None:
                                info.attributes = other.attributes
                            else:
                                assert info.attributes == other.attributes

                # Update all node paths to point to the same info
                for p in fullPaths:
                    self._files[p] = info
                return info
            elif create and nodePaths:
                info = _P4FileInfo(nodePaths[0].path)
                for p in fullPaths:
                    self._files[p] = info
                return info
            else:
                return None
        else:
            # A single node path
            nodePath = nodePaths
            assert nodePath.rev is not None

            fullPath = nodePath.fullPath
            if fullPath in self._files:
                return self._files[fullPath]
            elif create:
                info = _P4FileInfo(nodePath.path)
                self._files[fullPath] = info
                return info
            else:
                return None

    def _runDescribe(self, changes):
        """Run 'p4 describe' on each of the changelist numbers in C{changes}
        and record the results in the internal cache.

        @param changes: A sequence of change numbers to query and populate
        in the repository cache.
        @type: C{sequence} of C{int}
        """

        args = [str(int(x)) for x in changes]
        output = _P4DescribeOutputConsumer(self)
        results = self._connection.run('describe', '-s',
                                       output=output,
                                       *args)
        if output.errors:
            raise PerforceError(output.errors)

    def _runDirs(self, nodePath, subdirs=False):
        """Run 'p4 dirs' on the specified node path.

        @param nodePath: The path of the directory to query.
        @type nodePath: L{P4NodePath}

        @param subdirs: Flag indicating whether to query for the specified
        node path or for subdirectories of the specified node path.
        """

        assert nodePath.rev is not None
        if subdirs:
            if nodePath.isRoot:
                if self._connection.client != NO_CLIENT:
                    query = u'//%s/*%s' % (self._connection.client, nodePath.rev)
                else:
                    query = u'//*%s' % nodePath.rev
            else:
                query = u'%s/*%s' % (nodePath.path, nodePath.rev)
            self._log.debug("_rundirs '%s' " % query)
        else:
            query = unicode(nodePath)

        output = _P4DirsOutputConsumer(self, nodePath.rev)
        results = self._connection.run('dirs',
                                       self.fromUnicode(query),
                                       output=output)

        # If this was a subdirectory listing query then we populate the
        # directory's list of subdirectories.
        if subdirs:
            dirInfo = self._getDirInfo(nodePath,
                                       create=output.dirs)
            if dirInfo is not None:
                dirInfo.subdirs = [np.leaf for np in output.dirs]
                if self._connection.client != NO_CLIENT:
                    dirInfo.path = u'//%s/' % self._connection.client
                self._log.debug("sub dirs '%s %s %s %s' " % (dirInfo.path, dirInfo.subdirs, dirInfo.files, dirInfo.change))
        if output.errors:
            raise PerforceError(output.errors)

    def _runFstat(self, nodePath, wildcard=None):
        """Run 'p4 fstat' on the specified node path.

        @param nodePath: The path to query for file info.
        @type nodePath: L{P4NodePath}

        @param wildcard: The wildcard to apply to the nodePath.
        May be either C{u'*'}, for all files in the directory, C{u'...'} for
        all files under the directory or C{None} for the named file only.
        """

        assert nodePath.rev is not None

        if wildcard is None:
            queryPath = nodePath.fullPath
        else:
            assert wildcard in [u'*', u'...']
            if nodePath.isRoot:
                if self._connection.client != NO_CLIENT:
                    queryPath = u'//%s/%s' % (self._connection.client, wildcard)
                else:
                    queryPath = u'//%s' % wildcard
            else:
                queryPath = u'%s/%s%s' % (nodePath.path,
                                          wildcard,
                                          nodePath.rev)

        output = _P4FstatOutputConsumer(self, nodePath.rev)

        if self.getServerVersion() >= 20:
            # 2005.2 or later
            self._connection.run('fstat',
                                 '-Os', # Ingore client details
                                 '-Ol', # File size + digest
                                 '-Oa', # Attributes
                                 self.fromUnicode(queryPath),
                                 output=output)
        elif self.getServerVersion() >= 18:
            # 2005.1 (and 2004.2?) has a bug that suppresses the fileSize
            # field if both -Ol and -Os are specified.
            self._connection.run('fstat',
                                 '-Ol', # File size + digest
                                 '-Oa', # Attributes
                                 self.fromUnicode(queryPath),
                                 output=output)
        else:
            # Pre 2004.2 doesn't support -O flags
            self._connection.run('fstat',
                                 '-l',
                                 '-s',
                                 self.fromUnicode(queryPath),
                                 output=output)

        # If the request was for //path/to/dir/* then we need to populate
        # the list of files under that directory.
        if wildcard == u'*':
            dirInfo = self._getDirInfo(nodePath)
            if dirInfo is not None and dirInfo.files is None:
                dirInfo.files = [f[f.rfind(u'/')+1:]
                                 for f in output.files]
            
        if output.errors:
            raise PerforceError(output.errors)

    def _runFileLog(self, nodePath, maxRevisions=None, wildcard=None):
        """Run 'p4 filelog' on the node path to populate the repository with
        the file history for that node.

        @param nodePath: The node path of the node to query the file history
        for. If the node is a directory then wildcard parameter is also
        required.

        @param maxRevisions: The maximum number of revisions 
        """
        
        assert nodePath.rev is not None

        args = ['-l', '-i']
        if maxRevisions is not None:
            args.extend(['-m', str(maxRevisions)])
        if wildcard is None:
            queryPath = nodePath.fullPath
        else:
            if nodePath.isRoot:
                if self._connection.client != NO_CLIENT:
                    queryPath = u'//%s/%s' % (self._connection.client, wildcard)
                else:
                    queryPath = u'//%s' % wildcard
            else:
                queryPath = u'%s/%s%s' % (nodePath.path,
                                          wildcard,
                                          nodePath.rev)
        args.append(self.fromUnicode(queryPath))

        output = _P4FileLogOutputConsumer(self)
        self._connection.run('filelog', output=output, *args)
        if output.errors:
            raise PerforcError(output.errors)

    def _runChanges(self, nodePath, maxChanges=None, wildcard=None):
        """Run 'p4 changes' on the node path to look for submitted changes
        that affect the specified node.

        @param nodePath: The node path to query for changes.

        @param maxChanges: If specified then only look for at most this many
        most recent changes.
        @type maxChanges: C{int} or C{None}

        @param wildcard: If specified then search for changes that affect
        files matching this wildcard under the nodePath. This is typically
        either C{u'*'} or C{u'...'}.
        @type wildcard: C{unicode} or C{None}
        """

        assert nodePath.rev is not None

        args = ['-l', '-s', 'submitted']
        if maxChanges is not None:
            args.extend(['-m', str(maxChanges)])
        if wildcard is None:
            queryPath = nodePath.fullPath
        else:
            if nodePath.isRoot:
                if self._connection.client != NO_CLIENT:
                    queryPath = u'//%s/%s%s' % (self._connection.client,
                                             wildcard,
                                             nodePath.rev)
                else:
                    queryPath = u'//%s%s' % (wildcard,
                                             nodePath.rev)
            else:
                queryPath = u'%s/%s%s' % (nodePath.path,
                                          wildcard,
                                          nodePath.rev)
        args.append(self.fromUnicode(queryPath))

        output = P4ChangesOutputConsumer(self)
        self._connection.run('changes', output=output, *args)

        if wildcard == u'...':
            # It's a 'p4 changes //path/to/dir/...' request
            # Populate that directory's change
            
            if output.changes:
                latestChange = max(output.changes)
                changeNodePath = P4NodePath(nodePath.path, latestChange)
                info = self._getDirInfo([nodePath, changeNodePath],
                                        create=True)
                info.change = latestChange
            elif not output.errors:
                info = self._getDirInfo(nodePath)
                if info is not None:
                    info.change = 0

        if output.errors:
            raise PerforceError(output.errors)


class P4ChangesOutputConsumer(object):
    """Output consumer for 'p4 changes' commands."""

    protocols.advise(
        instancesProvide=[IOutputConsumer]
        )

    def __init__(self, repository):
        self.repository = repository
        self.changes = []
        self.errors = []

    def outputRecord(self, record):
        change = int(record['change'])
        self.changes.append(change)

        info = self.repository._getChangeInfo(change, create=True)
        if info.status is None:
            info.status = self.repository.toUnicode(record['status'])
        if info.client is None:
            info.client = self.repository.toUnicode(record['client'])
        if info.user is None:
            info.user = self.repository.toUnicode(record['user'])
        if info.time is None:
            info.time = int(record['time'])
        if info.description is None:
            info.description = self.repository.toUnicode(record['desc'])

    def outputMessage(self, message):
        if message.isError():
            self.errors.append(message)

    def _doNothing(self, *args, **kw):
        pass

    outputForm = _doNothing
    outputBinary = _doNothing
    outputText = _doNothing
    finished = _doNothing


class _P4DescribeOutputConsumer(object):
    """Output consumer for 'p4 describe' commands."""

    protocols.advise(
        instancesProvide=[IOutputConsumer]
        )

    def __init__(self, repository):
        self.repository = repository
        self.errors = []

    def outputRecord(self, record):
        change = int(record['change'])
        info = self.repository._getChangeInfo(change, create=True)
        if info.status is None:
            info.status = self.repository.toUnicode(record['status'])
        if info.client is None:
            info.client = self.repository.toUnicode(record['client'])
        if info.user is None:
            info.user = self.repository.toUnicode(record['user'])
        if info.time is None:
            info.time = int(record['time'])
        if info.description is None:
            info.description = self.repository.toUnicode(record['desc'])

        filePaths = []
        i = 0
        while 'depotFile%i' % i in record:
            path = self.repository.toUnicode(record['depotFile%i' % i])
            rev = int(record['rev%i' % i])
            filePaths.append(path)

            nodePathFile = P4NodePath(path, u'#%i' % rev)
            nodePathRepo = P4NodePath(path, u'@%i' % change)
            fileInfo = self.repository._getFileInfo([nodePathFile,
                                                     nodePathRepo],
                                                    create=True)

            if fileInfo.rev is None:
                fileInfo.rev = rev
            if fileInfo.change is None:
                fileInfo.change = change
            if fileInfo.action is None:
                fileInfo.action = self.repository.toUnicode(record['action%i' % i])
            if fileInfo.type is None:
                fileInfo.type = self.repository.toUnicode(record['type%i' % i])

            if fileInfo.action != u'delete':
                # The file exists at this change
                # We can infer that all parent node paths exist at this change
                # number, so force their creation.
                parentNodePath = P4NodePath(nodePathRepo.parent, change)
                while not parentNodePath.isRoot:
                    self.repository._getDirInfo(parentNodePath, create=True)
                    parentNodePath = P4NodePath(parentNodePath.parent, change)

            i += 1

        if info.files is None:
            info.files = filePaths

    def outputMessage(self, message):
        if message.isError():
            self.errors.append(message)

    def _doNothing(self, *args, **kw):
        pass

    outputForm = _doNothing
    outputBinary = _doNothing
    outputText = _doNothing
    finished = _doNothing

    
class _P4DirsOutputConsumer(object):
    protocols.advise(
        instancesProvide=[IOutputConsumer]
        )

    def __init__(self, repository, revision):
        self.repository = repository
        self.revision = revision
        self.dirs = []
        self.errors = []

    def outputRecord(self, record):
        from p4trac.util import toUnicode
        path = self.repository.toUnicode(record['dir'])
        nodePath = P4NodePath(path, self.revision)
        self.dirs.append(nodePath)

        # Force creation of the directory info
        self.repository._getDirInfo(nodePath, create=True)

    def outputMessage(self, message):
        if message.isError():
            self.errors.append(message)

    def _doNothing(self, *args, **kw):
        pass

    outputForm = _doNothing
    outputBinary = _doNothing
    outputText = _doNothing
    finished = _doNothing


class _P4FstatOutputConsumer(object):
    protocols.advise(
        instancesProvide=[IOutputConsumer]
        )

    def __init__(self, repository, revision):
        self.repository = repository
        self.revision = revision
        self.files = []
        self.errors = []

    def outputRecord(self, record):
        path = self.repository.toUnicode(record['depotFile'])
        rev = int(record['headRev'])
        change = int(record['headChange'])

        nodePathFile = P4NodePath(path, '#%i' % rev)
        nodePathRepo = P4NodePath(path, '@%i' % change)
        nodePathQuery = P4NodePath(path, self.revision)
        info = self.repository._getFileInfo([nodePathFile,
                                             nodePathRepo,
                                             nodePathQuery],
                                            create=True)

        if info.rev is None:
            info.rev = rev
        if info.change is None:
            info.change = change
        if info.action is None:
            info.action = self.repository.toUnicode(record['headAction'])
        if info.type is None:
            info.type = self.repository.toUnicode(record['headType'])
        if info.attributes is None:
            info.attributes = {}
            for key, value in record.iteritems():
                key = self.repository.toUnicode(key)
                if key.startswith(u'attr-'):
                    name = key[5:]
                    info.attributes[name] = self.repository.toUnicode(value)
        if info.size is None:
            # Note: size may not be present if the action is 'delete'.
            if 'fileSize' in record:
                info.size = int(record['fileSize'])
        if info.size is not None:
            # The file exists at this change
            self.files.append(path)
            # We can infer that all parent node paths exist at this change
            # number, so force the directory info creation.
            parentNodePath = P4NodePath(nodePathRepo.parent, change)
            while not parentNodePath.isRoot:
                self.repository._getDirInfo(parentNodePath, create=True)
                parentNodePath = P4NodePath(parentNodePath.parent, change)

    def outputMessage(self, message):
        if message.isError():
            self.errors.append(message)

    def _doNothing(self, *args, **kw):
        pass

    outputForm = _doNothing
    outputBinary = _doNothing
    outputText = _doNothing
    finished = _doNothing

    
class _P4PrintOutputConsumer(object):
    """Writes output of a 'p4 print' command to a Python file-like object."""

    protocols.advise(
        instancesProvide=[IOutputConsumer],
        )

    def __init__(self, file):
        self.file = file
        self.errors = []

    def outputBinary(self, data):
        self.file.write(data)

    def outputText(self, data):
        self.file.write(data)

    def outputMessage(self, message):
        if message.isError():
            self.errors.append(message)

    def finished(self):
        self.file.flush()

    def _doNothing(self, *args, **kw):
        pass

    outputRecord = _doNothing
    outputForm = _doNothing


class _P4FileLogOutputConsumer(object):
    """Stores output of 'p4 filelog' commands in the repository's cache."""

    protocols.advise(
        instancesProvide=[IOutputConsumer],
        )

    def __init__(self, repository):
        self.repository = repository
        self.errors = []

    def outputMessage(self, message):
        if message.isError():
            self.errors.append(message)

    def outputRecord(self, record):
        from perforce.results import FileLog
        fileLog = FileLog.parseRecord(record)
        path = self.repository.toUnicode(fileLog.depotFile)

        for fileRev in fileLog.revisions:
            nodePathRepos = P4NodePath(path, '@%i' % fileRev.change)
            nodePathFile = P4NodePath(path, '#%i' % fileRev.rev)

            change = fileRev.change
            changeInfo = self.repository._getChangeInfo(change, create=True)
            if changeInfo.description is None:
                changeInfo.description = self.repository.toUnicode(
                                                fileRev.desc)
            if changeInfo.time is None:
                changeInfo.time = fileRev.time
            if changeInfo.client is None:
                changeInfo.client = self.repository.toUnicode(fileRev.client)
            if changeInfo.user is None:
                changeInfo.user = self.repository.toUnicode(fileRev.user)

            fileInfo = self.repository._getFileInfo([nodePathRepos,
                                                     nodePathFile],
                                                    create=True)
            if fileInfo.rev is None:
                fileInfo.rev = int(fileRev.rev)
            if fileInfo.change is None:
                fileInfo.change = int(fileRev.change)
            if fileInfo.action is None:
                fileInfo.action = self.repository.toUnicode(fileRev.action)
            if fileInfo.sources is None:
                fileInfo.sources = []

                for integ in fileRev.integrations:
                    otherNodePath = P4NodePath(
                                        self.repository.toUnicode(integ.file),
                                        self.repository.toUnicode(integ.erev))

                    otherFileInfo = self.repository._getFileInfo(otherNodePath,
                                                                 create=True)
                    if otherFileInfo.rev is None:
                        otherFileInfo.rev = int(integ.erev[1:])

                    # Only interested in files that have contributed to this
                    # file, ignore information about other files this revision
                    # has been integrated into.
                    if integ.how == 'branch from':
                        how = u'branch'
                    elif integ.how == 'copy from':
                        how = u'copy'
                    elif integ.how == 'ignored':
                        how = u'ignore'
                    elif integ.how == 'delete from':
                        how = u'delete'
                    elif integ.how == 'edit from':
                        how = u'edit'
                    elif integ.how == 'merge from':
                        how = u'merge'
                    else:
                        how = None
                    if how is not None:
                        fileInfo.sources.append((otherNodePath, how))

    def _doNothing(self, *args, **kw):
        pass

    outputForm = _doNothing
    outputBinary = _doNothing
    outputText = _doNothing
    finished = _doNothing


class P4Diff2OutputConsumer(object):

    protocols.advise(
        instancesProvide=[IOutputConsumer],
        )

    # Parses lines of form:
    # ==== //path/to/file1#12 (type1) - //path/to/file2#34 (type2) ==== summary
    summaryLineRE = re.compile(
        ur'^=+\s*' + \
        ur'(?P<file1>' + \
        ur'(?:(?P<path1>//[^/]+/.+#\S+)(?:\s+\((?P<type1>.+)\))?)' + \
        ur'|' + \
        ur'(?:<\s*none\s*>)' + \
        ur')' + \
        ur'\s*-\s*' + \
        ur'(?P<file2>' + \
        ur'(?:(?P<path2>//[^/]+/.+#\S+)(?:\s+\((?P<type2>.+)\))?)' + \
        ur'|' + \
        ur'(?:<\s*none\s*>)' + \
        ur')' + \
        ur'\s*=+\s*' + \
        ur'(?P<summary>\S*)$'
        )

    def __init__(self, repository):
        self.repository = repository
        self.errors = []
        self.changes = []

    def outputMessage(self, message):
        if message.isError():
            self.errors.append(message)
        elif message.isInfo():
            line = self.repository.toUnicode(message.format())
            if line.startswith(u'==== '):
                match = self.summaryLineRE.match(line)
                if match:
                    file1 = match.group(u'file1')
                    path1 = match.group(u'path1')
                    file2 = match.group(u'file2')
                    path2 = match.group(u'path2')
                    summary = match.group(u'summary')
                    if summary != u'identical':
                        if path1:
                            i = path1.find(u'#')
                            nodePath1 = P4NodePath(path1[:i], path1[i:])
                        else:
                            nodePath1 = None

                        if path2:
                            i = path2.find(u'#')
                            nodePath2 = P4NodePath(path2[:i], path2[i:])
                        else:
                            nodePath2 = None

                        self.changes.append( (nodePath1, nodePath2) )

    def outputRecord(self, record):
        if record['status'] != 'identical':
            if 'depotFile' in record:
                path1 = self.repository.toUnicode(record['depotFile'])
                rev1 = self.repository.toUnicode(record['rev'])
                nodePath1 = P4NodePath(path1, u'#%s' % rev1)
            else:
                nodePath1 = None

            if 'depotFile2' in record:
                path2 = self.repository.toUnicode(record['depotFile2'])
                rev2 = self.repository.toUnicode(record['rev2'])
                nodePath2 = P4NodePath(path2, u'#%s' % rev2)
            else:
                nodePath2 = None
            self.changes.append( (nodePath1, nodePath2) )

    def _doNothing(self, *args, **kw):
        pass

    outputForm = _doNothing
    outputBinary = _doNothing
    outputText = _doNothing
    finished = _doNothing
