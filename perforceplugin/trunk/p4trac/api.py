# -*- coding: utf-8 -*-
#
# Authors: Lewis Baker <lewbaker99@hotmail.com>
#          Thomas Tressières <thomas.tressieres@free.fr>

import posixpath
from datetime import datetime

from trac.config import ListOption, Option
from trac.core import Component, implements, TracError
from trac.versioncontrol import Changeset, Node, Repository, \
                                Authorizer, IRepositoryConnector, \
                                NoSuchChangeset, NoSuchNode
from trac.versioncontrol.cache import CachedRepository
from trac.versioncontrol.web_ui.browser import IPropertyRenderer
from trac.util import sorted, embedded_numbers
from trac.util.text import to_unicode
from trac.util.datefmt import utc

from p4trac.repos import NO_CLIENT


def rootPath(connection):
    """Root path for quereis.
    If we have a client set, then we limit our queries to the client view.
    Otherwise we start from the very top.
    """
    if connection.client != NO_CLIENT:
        return '//%s/...' % connection.client
    else:
        return '//...'

def normalisePath(path):
    """Normalise a Perforce path and return it as a Trac-compatible path.

    If None or the empty string is passed then the root path is returned.
    The path is returned with a single leading slash rather than the Perforce
    depot notation which uses two leading slashes.

    @return: The normalised Perforce path.
    @rtype: C{unicode}
    """

    from p4trac.repos import P4NodePath
    path = P4NodePath.normalisePath(path)
    if path is None:
        return u'/'
    else:
        return path[1:]

def normaliseRev(rev):
    """Normalise a Perforce revision and return it as a Trac-compatible rev.

    Basically converts revisions to '@<label/client/date>' or '#<rev>' but
    returns '@<change>' as an integer value.
    """
    from p4trac.repos import P4NodePath
    rev = P4NodePath.normaliseRevision(rev)
    if rev is None:
        return rev
    elif rev.startswith(u'@') and rev[1:].isdigit():
        return int(rev[1:])
    else:
        return rev


class PerforceConnector(Component):
    """Component that registers the Perforce repository file system with
    the Trac repository manager.
    """

    implements(IRepositoryConnector)

    port = Option('perforce', 'port', 'localhost:1666', doc=
        """Perforce server IP address and port.
        """)
    user = Option('perforce', 'user', '', doc=
        """Perforce user name used to identify requests.
        """)
    password = Option('perforce', 'password', '', doc=
        """Perforce password used to identify requests.
        """)
    language = Option('perforce', 'language', '', doc=
        """Perforce language used for text message from the server.
        """)
    workspace = Option('perforce', 'workspace', NO_CLIENT, doc=
        """Perforce workspace used to request server.
        """)
    charset = Option('perforce', 'charset', 'none', doc=
        """Perforce charset used to request server.
        valid options are 'none', 'utf-8'.
        """)

    branches = ListOption('perforce', 'branches', 'main,branches/*', doc=
        """List of paths categorized as ''branches''.
        If a path ends with '*', then all the directory entries found
        below that path will be included.
        """)
    labels = ListOption('perforce', 'labels', 'labels/*', doc=
        """List of paths categorized as ''labels''.
        If a path ends with '*', then all the directory entries found
        below that path will be included.
        """)

    def __init__(self):
        try:
            import perforce
            self.log.debug('Perforce bindings imported')
        except ImportError:
            self.log.warning('Failed to import PyPerforce: ' + str(e))
            self.hasPerforce = False
        else:
            self.hasPerforce = True

    def get_supported_types(self):
        if self.hasPerforce:
            yield ("perforce", 4)

    def get_repository(self, repos_type, repos_dir, authname):
        """Return a `PerforceRepository`.

        The repository is wrapped in a `CachedRepository`.
        """

        assert repos_type == 'perforce'

        self.log.debug("get_repository dir : %s" % (repos_dir))
        options = dict(self.config.options('perforce'))
        self.log.debug("get_repository options : %s" % (options))

        # Try to connect to the Perforce server
        from perforce import Connection, ConnectionFailed
        p4 = Connection(port=self.port, api='58') # Limit to 2005.2 behaviour
        try:
            from trac import __version__ as tracVersion
            p4.connect(prog='Trac', version=tracVersion)
        except ConnectionFailed:
            raise TracError(
                message="Could not connect to Perforce repository.",
                title="Perforce connection error")

        if self.user == '':
            raise TracError(
                message="Missing 'user' value in [perforce] config section.",
                title="Perforce configuration error")
        p4.user = self.user
        p4.password = self.password
        p4.charset = self.charset
        p4.language = self.language
        jobPrefixLength = len(options.get('job_prefix', 'job'))
        p4.client = self.workspace

        p4_repos = PerforceRepository(p4, None, self.log, jobPrefixLength,
                                      {'labels': self.labels,
                                       'branches': self.branches})
        repos = CachedRepository(self.env.get_db_cnx(), p4_repos, None, self.log)
        if authname:
            pass
        return repos


class PerforcePropertyRenderer(Component):
    implements(IPropertyRenderer)

    def match_property(self, name, mode):
        return name in ('Tickets') and 4 or 0

    def render_property(self, name, mode, context, props):
        import string
        from genshi.builder import tag
        fragments = []
        vals = string.split(props[name], ' ')
        for val in vals[1:]:
            title = "ticket %s" % (val)
            fragments.append(tag.a("#%s" % val, class_="ticket",
                                   title=title,
                                   href=context.href.ticket(val)))
        return tag([tag(f, ', ') for f in fragments[:-1]], fragments[-1])


class PerforceRepository(Repository):
    """A Perforce repository implementation.

    Built on top of the PyPerforce API.
    http://pyperforce.sourceforge.net/
    """

    def __init__(self, connection, authz, log, jobPrefixLength, options={}):
        self._job_prefix_length = jobPrefixLength
        self.options = options
        self._connection = connection
        name = 'p4://%s@%s' % (connection.user, connection.port)
        Repository.__init__(self, name, authz, log)
        from p4trac.repos import P4Repository
        self._repos = P4Repository(connection, log)

    def __del__(self):
        self.close()

    def clear(self, youngest_rev=None):
        self.youngest = None
        if youngest_rev is not None:
            self.youngest = self.normalize_rev(youngest_rev)
        self.oldest = None

    def close(self):
        self._connection.disconnect()

    def _get_labels_or_branches(self, paths):
        """Retrieve known branches or labels."""
        for path in self.options.get(paths, []):
            self.log.debug('_get_labels_or_branches %s' % path)
            if path.endswith('*'):
                folder = posixpath.dirname(path)
                try:
                    entries = [n for n in self.get_node(folder).get_entries()]
                    for node in sorted(entries, key=lambda n: 
                                       embedded_numbers(n.path.lower())):
                        if node.kind == Node.DIRECTORY:
                            yield node
                except: # no right (TODO: should use a specific Exception here)
                    pass
            else:
                try:
                    yield self.get_node(path)
                except: # no right
                    pass

    def get_quickjump_entries(self, rev):
        """Retrieve known branches, as (name, id) pairs.
        
        Purposedly ignores `rev` and always takes the last revision.
        """
        self.log.debug('get_quickjump_entries(%r)' % rev)
        for n in self._get_labels_or_branches('branches'):
            self.log.debug('get_quickjump_entries branches: %s' % n.path)
            yield 'branches', n.path, n.path, None
        for n in self._get_labels_or_branches('labels'):
            self.log.debug('get_quickjump_entries labels: %s' % n.path)
            yield 'labels', n.path, n.created_path, n.created_rev

    def get_changeset(self, rev):
        self.log.debug('PerforceRepository.get_changeset(%r)' % rev)
        if isinstance(rev, int):
            change = rev
        else:
            from p4trac.util import toUnicode
            rev = toUnicode(rev)
            if rev.startswith(u'@'):
                rev = rev[1:]
            try:
                change = int(rev)
            except ValueError:
                raise TracError(u"Invalid changeset number '%s'" % rev)
        return PerforceChangeset(change, self._repos, self.log, self._job_prefix_length)

    def get_changesets(self, start, stop):
        self.log.debug('PerforceRepository.get_changesets(%r,%r)' % (start,
                                                                      stop))
        import datetime
        start = datetime.datetime.fromtimestamp(start)
        stop = datetime.datetime.fromtimestamp(stop)
        startDate = start.strftime('%Y/%m/%d:%H:%M:%S')
        stopDate = stop.strftime('%Y/%m/%d:%H:%M:%S')

        from p4trac.repos import P4ChangesOutputConsumer
        output = P4ChangesOutputConsumer(self._repos)
        depot_path = '%s@>=%s,@<=%s' % (rootPath(self._connection), startDate, stopDate)
        self._connection.run('changes', '-l', '-s', 'submitted',
                             depot_path, output=output)
        if output.errors:
            from p4trac.repos import PerforceError
            raise PerforceError(output.errors)

        for change in output.changes:
            yield self.get_changeset(change)

    def has_node(self, path, rev=None):
        from p4trac.repos import P4NodePath
        path = P4NodePath.normalisePath(path)
        return self._repos.getNode(P4NodePath(path, rev)).exists

    def get_node(self, path, rev=None):
        self.log.debug('get_node(%s, %s) called' % (path, rev))
        from p4trac.repos import P4NodePath
        nodePath = P4NodePath(P4NodePath.normalisePath(path), rev)
        return PerforceNode(nodePath, self._repos, self.log)

    def get_oldest_rev(self):
        return self.next_rev(0, '')

    def get_youngest_rev(self):
        return self._repos.getLatestChange()

    def previous_rev(self, rev, path):
        self.log.debug('previous_rev(%r)' % rev)
        if not isinstance(rev, int):
            rev = self.short_rev(rev)
            if not isinstance(rev, int):
                raise NoSuchChangeset(rev)

        from p4trac.repos import P4ChangesOutputConsumer
        output = P4ChangesOutputConsumer(self._repos)
        self._connection.run('changes', '-l', '-s', 'submitted',
                             '-m', '1', '@<%i' % rev, output=output)
        if output.errors:
            from p4trac.repos import PerforceError
            raise PerforceError(output.errors)
        if output.changes:
            return max(output.changes)
        else:
            return None

    def next_rev(self, rev, path=''):
        # Finding the next revision is a little more difficult in Perforce
        # as we can only ask for the n most recent changes according to a
        # given criteria. We query batches of changes using a binary search
        # technique so that the number of changes queried is of the order of
        # log N where N is the number of changes greater than rev. This way
        # it is still fairly efficient if the next change is 1 or 1000 changes
        # later.
        self.log.debug('next_rev(%r,%r)' % (rev, path))

        from p4trac.repos import P4NodePath
        if not path:
            path = u'//'
        else:
            path = P4NodePath.normalisePath(path)
        node = self._repos.getNode(P4NodePath(path, rev))
        self.log.debug(u'node : %i %i %s' % (node.isDirectory, node.nodePath.isRoot, node.nodePath.path))

        if node.isDirectory:
            if node.nodePath.isRoot:
                # Handle the root path specially since it encompasses all
                # changes and so can use the repository's internal cache.
                return self._repos.getNextChange(int(rev))
            else:
                queryPath = u'%s/...' % node.nodePath.path
        else:
            queryPath = node.nodePath.path

        queryPath = self._repos.fromUnicode(queryPath)
        self.log.debug(u'Looking for next_rev after change %i for %s' % (rev, path))

        # Perform a binary-search of sorts for the next revision
        batchSize = 50
        lowerBound = rev + 1
        upperBound = self.youngest_rev

        while lowerBound <= upperBound:
            if lowerBound + batchSize > upperBound:
                batchUpperBound = upperBound
            else:
                middle = (upperBound + lowerBound) / 2
                if middle - lowerBound < batchSize:
                    batchUpperBound = lowerBound + batchSize
                else:
                    batchUpperBound = middle
            self.log.debug(
                'Looking for changes in range [%i, %i]' % (lowerBound,
                                                           batchUpperBound))

            from p4trac.repos import P4ChangesOutputConsumer
            output = P4ChangesOutputConsumer(self._repos)
            depot_path = '%s%s@>=%i,@<=%i' % (rootPath(self._connection),
                                              queryPath, lowerBound, batchUpperBound)
            self._connection.run('changes', '-l', '-s', 'submitted',
                                 '-m', str(batchSize),
                                 depot_path, output=output)

            if output.errors:
                from p4trac.repos import PerforceError
                raise PerforceError(output.errors)

            if output.changes:
                lowest = min(output.changes)
                assert lowest >= lowerBound
                assert lowest <= batchUpperBound

                if lowerBound + batchSize >= batchUpperBound:
                    # There are no earlier changes
                    self.log.debug('next_rev is %i' % lowest)
                    return lowest
                else:
                    # There may be another earlier changes but we know it
                    # can't be any later than lowest.
                    upperBound = lowest
            else:
                # Didn't find any changes in (lowerBound, batchUpperBound)
                # Try searching from batchUpperBound + 1 onwards
                lowerBound = batchUpperBound + 1
        return None

    def rev_older_than(self, rev1, rev2):
        self.log.debug('PerforceRepository.rev_older_than(%r,%r)' % (rev1, rev2))

        rev1 = self.short_rev(rev1)
        rev2 = self.short_rev(rev2)

        # Can compare equal revisions directly
        if rev1 == rev2:
            return False

        # Can compare change revisions directly
        if isinstance(rev1, int) and isinstance(rev2, int):
            return rev1 < rev2

        def parseDateRevision(rev):
            if not isinstance(rev, unicode):
                raise ValueError
            if not rev.startswith(u'@'):
                raise ValueError
            # @YYYY/MM/DD[:HH:MM:SS]
            if len(rev) not in [11, 20]:
                raise ValueError
            year = int(rev[1:5])
            month = int(rev[6:8])
            day = int(rev[9:11])

            if rev[5] != u'/' or rev[8] != u'/':
                raise ValueError

            if len(rev) == 20:
                hour = int(rev[12:14])
                minute = int(rev[15:17])
                second = int(rev[18:20])

                if rev[11] != u':' or rev[14] != u':' or rev[17] != u':':
                    raise ValueError
            else:
                hour = 0
                minute = 0
                second = 0
            return (year, month, day, hour, minute, second)

        # Can compare date revisions directly
        try:
            return parseDateRevision(rev1) < parseDateRevision(rev2)
        except ValueError:
            pass

        # Can't compare these revisions directly,
        # Compare based on the latest change number that affects this revision.
        from p4trac.repos import P4NodePath
        if not isinstance(rev1, int):
            rootAtRev1 = P4NodePath(u'//', rev1)
            rev1 = self._repos.getNode(rootAtRev1).change
        if not isinstance(rev2, int):
            rootAtRev2 = P4NodePath(u'//', rev2)
            rev2 = self._repos.getNode(rootAtRev2).change
        self.log.debug('Comparing by change rev1=%i, rev2=%i' % (rev1, rev2))
        return rev1 < rev2

    def get_path_history(self, path, rev=None, limit=None):
        # TODO: This doesn't handle the case where the head node has been
        # deleted or a file has changed to a directory or vica versa.
        from p4trac.repos import P4NodePath
        nodePath = P4NodePath(P4NodePath.normalisePath(path), rev)
        node = PerforceNode(nodePath, self._repos, self.log)
        return node.get_history(limit)

    def normalize_path(self, path):
        self.log.debug('normalize_path(%r)' % path)
        return normalisePath(path)

    def normalize_rev(self, rev):
        self.log.debug('normalize_rev(%r)' % rev)
        rev = normaliseRev(rev)
        if rev is None:
            return self.youngest_rev
        else:
            return rev

    def short_rev(self, rev):
        self.log.debug('short_rev(%r)' % rev)
        return self.normalize_rev(rev)

    def get_changes(self, old_path, old_rev, new_path, new_rev, ignore_ancestry=0):
        self.log.debug('PerforceRepository.get_changes(%r,%r,%r,%r)' % (
                       old_path, old_rev, new_path, new_rev))

        from p4trac.repos import P4NodePath
        oldNodePath = P4NodePath(P4NodePath.normalisePath(old_path), old_rev)
        oldNode = self._repos.getNode(oldNodePath)

        newNodePath = P4NodePath(P4NodePath.normalisePath(new_path), new_rev)
        newNode = self._repos.getNode(newNodePath)

        if (newNode.isFile and oldNode.isDirectory) or \
           (newNode.isDirectory and oldNode.isFile):
            raise TracError("Cannot view changes between directory and file")

        if newNode.isDirectory or oldNode.isDirectory:
            if oldNodePath.isRoot:
                oldQueryPath = u'%s%s' % (rootPath(self._connection),
                                          oldNodePath.rev)
            else:
                oldQueryPath = u'%s/...%s' % (oldNodePath.path,
                                             oldNodePath.rev)
            if newNodePath.isRoot:
                newQueryPath = u'%s%s' % (rootPath(self._connection),
                                          newNodePath.rev)
            else:
                newQueryPath = u'%s/...%s' % (newNodePath.path,
                                             newNodePath.rev)
        elif newNode.isFile or oldNode.isFile:
            oldQueryPath = oldNodePath.fullPath
            newQueryPath = newNodePath.fullPath
        else:
            raise TracError("Cannot diff two non-existant nodes")

        from p4trac.repos import P4Diff2OutputConsumer
        output = P4Diff2OutputConsumer(self._repos)

        self._connection.run('diff2', '-ds',
                             self._repos.fromUnicode(oldQueryPath),
                             self._repos.fromUnicode(newQueryPath),
                             output=output)
        if output.errors:
            from p4trac.repos import PerforceError
            raise PerforceError(output.errors)

        for change in output.changes:
            oldFileNodePath, newFileNodePath = change
            if oldFileNodePath is not None:
                oldFileNode = PerforceNode(oldFileNodePath,
                                           self._repos,
                                           self.log)
            else:
                oldFileNode = None

            if newFileNodePath is not None:
                newFileNode = PerforceNode(newFileNodePath,
                                           self._repos,
                                           self.log)
            else:
                newFileNode = None

            if newFileNode and oldFileNode:
                yield oldFileNode, newFileNode, Node.FILE, Changeset.EDIT
            elif newFileNode:
                yield oldFileNode, newFileNode, Node.FILE, Changeset.ADD
            elif oldFileNode:
                yield oldFileNode, newFileNode, Node.FILE, Changeset.DELETE


class PerforceNode(Node):
    """A Perforce repository node (depot, directory or file)"""

    def __init__(self, nodePath, repos, log):
        log.debug('Creation of PerforceNode for %r' % nodePath)
        self._log = log
        self._nodePath = nodePath
        self._repos = repos
        self._node = self._repos.getNode(nodePath)
        node_type = self._get_kind()
        self.created_rev = self._node.change
        self.created_path = self._nodePath.path
        self.rev = self.created_rev
        Node.__init__(self, self._nodePath.path, self.rev, node_type)

    def _get_kind(self):
        if self._node.isDirectory:
            return Node.DIRECTORY
        elif self._node.isFile:
            return Node.FILE
        else:
            raise NoSuchNode(self._nodePath.path, self._nodePath.rev)

    def get_content(self):
        self._log.debug('PerforceNode.get_content()')
        return self._node.fileContent

    def get_entries(self):
        self._log.debug('PerforceNode.get_entries()')
        if self.isdir:
            for node in self._node.subDirectories:
                self._log.debug('got subddir %s' % node.nodePath.fullPath)
                yield PerforceNode(node.nodePath, self._repos, self._log)

            for node in self._node.files:
                self._log.debug('got file %s' % node.nodePath.fullPath)
                yield PerforceNode(node.nodePath, self._repos, self._log)

    def get_history(self, limit=None):
        self._log.debug('PerforceNode.get_history(%r)' % limit)
        if self._node.isFile:
            # Force population of the filelog history for efficiency
            self._repos._runFileLog(self._nodePath, limit)

            from p4trac.repos import P4NodePath

            currentNode = self._node
            i = 0
            while i < limit and currentNode is not None:
                if currentNode.action in [u'add', u'branch', u'import']:
                    if currentNode.integrations:
                        nodePath, how = currentNode.integrations[0]

                        # TODO: Detect whether the copy was really a move
                        yield (normalisePath(currentNode.nodePath.path),
                               currentNode.change,
                               Changeset.COPY)
                        currentNode = self._repos.getNode(nodePath)
                    else:
                        yield(normalisePath(currentNode.nodePath.path),
                              currentNode.change,
                              Changeset.ADD)
                        if currentNode.fileRevision > 1:
                            # Get the previous revision
                            nodePath = P4NodePath(currentNode.nodePath.path,
                                                  '#%i' % (currentNode.fileRevision - 1))
                            currentNode = self._repos.getNode(nodePath)
                        else:
                            currentNode = None
                elif currentNode.action in [u'edit', u'integrate']:
                    nextNode = None
                    if currentNode.integrations:
                        nodePath, how = currentNode.integrations[0]
                        if how == 'copy':
                            yield (normalisePath(currentNode.nodePath.path),
                                   currentNode.change,
                                   Changeset.COPY)
                            nextNode = self._repos.getNode(nodePath)
                        else:
                            yield (normalisePath(currentNode.nodePath.path),
                                   currentNode.change,
                                   Changeset.EDIT)
                    else:
                        yield (normalisePath(currentNode.nodePath.path),
                               currentNode.change,
                               Changeset.EDIT)
                    if nextNode is None:
                        if currentNode.fileRevision > 1:
                            currentNode = self._repos.getNode(
                                P4NodePath(currentNode.nodePath.path,
                                           '#%i' % (currentNode.fileRevision - 1)))
                        else:
                            currentNode = None
                    else:
                        currentNode = nextNode
                elif currentNode.action in [u'delete']:
                    yield (normalisePath(currentNode.nodePath.path),
                           currentNode.change,
                           Changeset.DELETE)
                    if currentNode.fileRevision > 1:
                        currentNode = self._repos.getNode(
                            P4NodePath(currentNode.nodePath.path,
                                       '#%i' % (currentNode.fileRevision - 1)))
                    else:
                        currentNode = None
                i += 1
        elif self._node.isDirectory:
            # List all changelists that have affected this directory
            from p4trac.repos import P4ChangesOutputConsumer
            output = P4ChangesOutputConsumer(self._repos)

            if self._nodePath.isRoot:
                queryPath = '@<=%s' % self._nodePath.rev[1:]
            else:
                queryPath = '%s/...@<=%s' % (self._nodePath.path, self._nodePath.rev[1:])

            if limit is None:
                self._repos._connection.run('changes', '-l', '-s', 'submitted',
                                            self._repos.fromUnicode(queryPath),
                                            output=output)
            else:
                self._repos._connection.run('changes', '-l', '-s', 'submitted',
                                            '-m', str(limit),
                                            self._repos.fromUnicode(queryPath),
                                            output=output)
            if output.errors:
                raise PerforceError(output.errors)
            changes = output.changes

            self._repos._runDescribe(changes)

            from p4trac.repos import P4NodePath
            for i in xrange(len(changes)):
                change = changes[i]
                nodePath = P4NodePath(self._nodePath.path, change)
                if i < len(changes)-1:
                    prevChange = changes[i+1]
                else:
                    prevChange = change-1

                prevNodePath = P4NodePath(self._nodePath.path, prevChange)
                node = self._repos.getNode(nodePath)
                prevNode = self._repos.getNode(prevNodePath)
                if node.isDirectory:
                    if prevNode.isDirectory:
                        yield (normalisePath(self._nodePath.path),
                               change,
                               Changeset.EDIT)
                    else:
                        yield (normalisePath(self._nodePath.path),
                               change,
                               Changeset.ADD)
                elif prevNode.isDirectory:
                    yield (normalisePath(self._nodePath.path),
                           change,
                           Changeset.DELETE)
        else:
            raise NoSuchNode(self._nodePath.path, self._nodePath.rev)

    def get_annotations(self):
        self._log.debug('PerforceNode.get_annotations')
        annotations = []
        if self.isfile:
            def blame_receiver(line_no, revision, author, date, line, pool):
                annotations.append(revision)
            try:
                pass
            except (AttributeError), e:
                # p4 thinks file is a binary or blame not supported
                raise TracError(_('p4 annotate failed: %(error)s',
                                  error=to_unicode(e)))
        return annotations

    def get_properties(self):
        self._log.debug('PerforceNode.get_properties')
        if self.kind is Node.FILE:
            props = { 'type' : self._node.type }
            props.update(self._node.attributes)
            return props
        else:
            # Directories have no properties
            return {}

    def get_content_length(self):
        self._log.debug('PerforceNode.get_content_length')
        if self.isdir:
            return None
        else:
            return self._node.fileSize

    def get_content_type(self):
        if self._node.isFile:
            if u'mime-type' in self._node.attributes:
                return self._node.attributes[u'mime-type']
        return None

    def get_name(self):
        return self._nodePath.leaf

    def get_last_modified(self):
        return self._repos.getChangelist(self._node.change).time


class PerforceChangeset(Changeset):
    """A Perforce repository changelist"""

    def __init__(self, change, repository, log, job_prefix_length):
        log.debug('PerforceChangeset(%r) created' % change)

        self._job_prefix_length = job_prefix_length
        self._change = int(change)
        self._repos = repository
        self._log = log
        self._changelist = self._repos.getChangelist(self._change)
        Changeset.__init__(self, self._change, self._changelist.description,
                           self._changelist.user,
                           datetime.fromtimestamp(self._changelist.time, utc))

    def get_properties(self):
        import p4trac.repos
        try:
            results = self._repos._connection.run('fixes', '-c', str(self._change))
            if results.errors:
                raise PerforceError(results.errors)

            props = {}
            fixes = ''
            for record in results.records:
                tktid = int(record['Job'][self._job_prefix_length:])
                self._log.debug("get_properties  %d " % tktid)
                fixes += ' %d' % tktid
            if fixes != '':
                props['Tickets'] = to_unicode(fixes)
            return props
        except p4trac.repos.NoSuchChangelist, e:
            raise NoSuchChangeset(e.change)

    def get_changes(self):
        # Force population of the file history for the files modified in this
        # changelist.
        self._log.debug("PerforceChangeset(%i).get_changes()" % self._change)
        self._repos.precacheFileInformationForChanges([self._change])

        for node in self._changelist.nodes:
            nodePath = node.nodePath
            self._log.debug('Change %i contains %s%s [%s]' % (self._change,
                                                              nodePath.path,
                                                              nodePath.rev,
                                                              node.action))

            if node.action in [u'add', u'branch', u'import']:
                if node.integrations:
                    otherNodePath, how = node.integrations[0]
                    otherNode = self._repos.getNode(otherNodePath)
                    yield (normalisePath(nodePath.path),
                           Node.FILE,
                           Changeset.COPY,
                           normalisePath(otherNodePath.path),
                           otherNode.change)
                else:
                    yield (normalisePath(nodePath.path),
                           Node.FILE,
                           Changeset.ADD,
                           None,
                           None)
            elif node.action in [u'edit', u'integrate']:
                if node.integrations and node.integrations[0][1] == 'copy':
                    otherNodePath, how = node.integrations[0]
                    otherNode = self._repos.getNode(otherNodePath)

                    # A 'copy from' operation
                    yield (normalisePath(nodePath.path),
                           Node.FILE,
                           Changeset.COPY,
                           normalisePath(otherNodePath.path),
                           otherNode.change)
                else:
                    if node.fileRevision > 1:
                        from p4trac.repos import P4NodePath
                        otherNode = self._repos.getNode(P4NodePath(nodePath.path,
                                                                   '#%i' % (node.fileRevision - 1)))

                        # A basic edit operation
                        yield (normalisePath(nodePath.path),
                               Node.FILE,
                               Changeset.EDIT,
                               normalisePath(nodePath.path),
                               otherNode.change)
                    else:
                        yield (normalisePath(nodePath.path),
                               Node.FILE,
                               Changeset.EDIT,
                               None,
                               None)
            elif node.action in [u'delete']:
                # The file was deleted
                from p4trac.repos import P4NodePath
                otherNodePath = P4NodePath(nodePath.path,
                                           '#%i' % (node.fileRevision - 1))
                otherNode = self._repos.getNode(otherNodePath)
                yield (normalisePath(nodePath.path),
                       Node.FILE,
                       Changeset.DELETE,
                       normalisePath(nodePath.path),
                       otherNode.change)
