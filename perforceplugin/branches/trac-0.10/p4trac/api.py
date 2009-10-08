from trac.core import Component, implements, TracError
from trac.versioncontrol import Changeset, Repository, Node, \
                                IRepositoryConnector, \
                                Authorizer, NoSuchChangeset, NoSuchNode
from trac.versioncontrol.cache import CachedRepository
from trac.util.text import to_unicode


def normalisePath(path):
    """Normalise a Perforce path and return it as a Trac-compatible path.

    If None or the empty string is passed then the root path is returned.
    The path is returned with a single leading slash rather than the Perforce
    depot notation which uses two leading slashes.

    @return: The normalised Perforce path.
    @rtype: C{unicode}
    """

    from p4trac.repos import NodePath
    path = NodePath.normalisePath(path)
    if path is None:
        return u'/'
    else:
        return path[1:]

def normaliseRev(rev):
    """Normalise a Perforce revision and return it as a Trac-compatible rev.

    Basically converts revisions to '@<label/client/date>' or '#<rev>' but
    returns '@<change>' as an integer value.
    """
    from p4trac.repos import NodePath
    rev = NodePath.normaliseRevision(rev)
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

    def get_supported_types(self):
        """Generate tuples of (name, priority)"""

        hasPerforce = False
        try:
            import perforce
            hasPerforce = True
        except ImportError, e:
            self.log.warning('Failed to import PyPerforce: ' + str(e))

        if hasPerforce:
            yield ('perforce', 4)

    def _update_option(self, options, key, value):
        """Update options dictionary with (key, value)"""
        if value == None:
            if key in options: del options[key]
        else:
            options[key] = value
        
    def _splitattributes(self, url):
        """_splitattr('attr1=value1&attr2=value2&...') ->
            ['attr1=value1', 'attr2=value2', ...]."""
        if url == None:
            return []
        words = url.split('&')
        return words

    def get_repository(self, repos_type, repos_dir, authname):

        assert repos_type == 'perforce'

        import urllib
        urltype, url = urllib.splittype(repos_dir)
        assert urltype == 'p4' or url == 'p4'

        options = dict(self.config.options('perforce'))
        if urltype != None:
            machine, path_query = urllib.splithost(url)
            user_passwd, host_port = urllib.splituser(machine)
            user, password = urllib.splitpasswd(user_passwd)
            self._update_option(options, 'port', host_port)
            self._update_option(options, 'password', password)
            self._update_option(options, 'user', user)

            path, query = urllib.splitquery(path_query)
            if path and path != '':
                for attr in self._splitattributes(query):
                    key, val = urllib.splitvalue(attr)
                    self._update_option(options, key, val)
            self._update_option(options, 'path', path)
            self.log.debug("get_repository options : %s" % (options))

        if 'port' not in options:
            raise TracError(
                message="Missing 'port' value in [perforce] config section.",
                title="TracPerforce configuration error",
                )

        # Try to connect to the Perforce server
        from perforce import Connection, ConnectionFailed
        p4 = Connection(port=options['port'],
                        api='58', # Limit to 2005.2 behaviour
                        )
        try:
            from trac import __version__ as tracVersion
            p4.connect(prog='Trac',
                       version=tracVersion)
        except ConnectionFailed:
            raise TracError(
                message="Could not connect to Perforce repository.",
                title="Perforce connection error",
                )

        if 'user' not in options:
            raise TracError(
                message="Missing 'user' value in [perforce] config section.",
                title="Perforce configuration error",
                )
        p4.user = options['user']

        if 'password' in options:
            p4.password = options['password']
        else:
            p4.password = ''

        if 'unicode' in options:
            if options['unicode'] == '1':
                p4.charset = 'utf8'
            elif options['unicode'] == '0':
                p4.charset = 'none'
            else:
                raise TracError(
                    message="Invalid 'unicode' value in [perforce] config " \
                    "section.",
                    title="Perforce configuration error",
                    )
        else:
            p4.charset = 'none'

        if 'language' in options:
            p4.language = options['language']
        else:
            p4.language = ''
            
        jobPrefixLength = 3 # default value because by default prefix is 'job'
        if 'job_prefix' in options:
            jobPrefixLength = len(options['job_prefix'])

        p4.client = ''

        repos = PerforceRepository(p4, None, self.log, jobPrefixLength)
        crepos = CachedRepository(self.env.get_db_cnx(), repos, None, self.log)
        return crepos


class PerforceRepository(Repository):
    """A Perforce repository implementation.

    Built on top of the PyPerforce API.
    http://pyperforce.sourceforge.net/
    """

    def __init__(self, connection, authz, log, jobPrefixLength):
        self._job_prefix_length = jobPrefixLength
        self._connection = connection
        name = 'p4://%s:%s@%s' % (self._connection.user, self._connection.password, self._connection.port)
        Repository.__init__(self, name, None, log)
        # The Repository object that we query for Perforce info
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

    def get_tags(self, rev):
        results = self._connection.run('labels')
        if results.errors:
            from p4trac.repos import PerforceError
            raise PerforceError(results.errors)
        for rec in results.records:
            name = self._repos.toUnicode(rec['label'])
            yield (name, u'@%s' % name)

    def get_branches(self, rev):
        # TODO: Generate a list of branches
        return []

    def get_changeset(self, rev):
        self.log.debug('get_changeset(%r)' % rev)
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
        self.log.debug('PerforceRepository.get_changesets(%r,%r)' % (start, stop))

        import datetime
        start = datetime.datetime.fromtimestamp(start)
        stop = datetime.datetime.fromtimestamp(stop)

        startDate = start.strftime('%Y/%m/%d:%H:%M:%S')
        stopDate = stop.strftime('%Y/%m/%d:%H:%M:%S')

        from p4trac.repos import _P4ChangesOutputConsumer
        output = _P4ChangesOutputConsumer(self._repos)
        self._connection.run('changes', '-l', '-s', 'submitted',
                             '@>=%s,@<=%s' % (startDate, stopDate),
                             output=output)
        if output.errors:
            from p4trac.repos import PerforceError
            raise PerforceError(output.errors)

        for change in output.changes:
            yield self.get_changeset(change)

    def has_node(self, path, rev=None):
        from p4trac.repos import NodePath
        path = NodePath.normalisePath(path)
        return self._repos.getNode(NodePath(path, rev)).exists

    def get_node(self, path, rev=None):
        self.log.debug('get_node(%s, %s) called' % (path, rev))
        from p4trac.repos import NodePath
        nodePath = NodePath(NodePath.normalisePath(path), rev)
        return PerforceNode(nodePath, self._repos, self.log)

    def get_oldest_rev(self):
        return self.next_rev(0)

    def get_youngest_rev(self):
        return self._repos.getLatestChange()

    def previous_rev(self, rev):
        self.log.debug('previous_rev(%r)' % rev)
        if not isinstance(rev, int):
            rev = self.short_rev(rev)
            if not isinstance(rev, int):
                raise NoSuchChangeset(rev)

        from p4trac.repos import _P4ChangesOutputConsumer
        output = _P4ChangesOutputConsumer(self._repos)
        self._connection.run('changes', '-l', '-s', 'submitted',
                             '-m', '1', '@<%i' % rev, output=output)
        if output.errors:
            from p4trac.repos import PerforcError
            raise PerforcError(output.errors)
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

        from p4trac.repos import NodePath
        if not path:
            path = u'//'
        else:
            path = NodePath.normalisePath(path)
        node = self._repos.getNode(NodePath(path, rev))

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
        self.log.debug(u'Looing for next_rev after change %i for %s' % (rev, path))

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
                    
            from p4trac.repos import _P4ChangesOutputConsumer
            output = _P4ChangesOutputConsumer(self._repos)
            self._connection.run('changes', '-l', '-s', 'submitted',
                                 '-m', str(batchSize),
                                 '%s@>=%i,@<=%i' % (queryPath,
                                                    lowerBound,
                                                    batchUpperBound),
                                 output=output)
            if output.errors:
                from p4trac.repos import PerforcError
                raise PerforcError(output.errors)
                
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
        from p4trac.repos import NodePath
        if not isinstance(rev1, int):
            rootAtRev1 = NodePath(u'//', rev1)
            rev1 = self._repos.getNode(rootAtRev1).change
        if not isinstance(rev2, int):
            rootAtRev2 = NodePath(u'//', rev2)
            rev2 = self._repos.getNode(rootAtRev2).change
        self.log.debug('Comparing by change rev1=%i, rev2=%i' % (rev1, rev2))
        return rev1 < rev2

    def get_path_history(self, path, rev=None, limit=None):
        # TODO: This doesn't handle the case where the head node has been
        # deleted or a file has changed to a directory or vica versa.
        from p4trac.repos import NodePath
        nodePath = NodePath(NodePath.normalisePath(path), rev)
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

    def get_changes(self, old_path, old_rev, new_path, new_rev, ignore_ancestry=1):
        self.log.debug('PerforceRepository.get_changes(%r,%r,%r,%r)' % (
            old_path, old_rev, new_path, new_rev))

        from p4trac.repos import NodePath
        oldNodePath = NodePath(NodePath.normalisePath(old_path), old_rev)
        oldNode = self._repos.getNode(oldNodePath)

        newNodePath = NodePath(NodePath.normalisePath(new_path), new_rev)
        newNode = self._repos.getNode(newNodePath)

        if (newNode.isFile and oldNode.isDirectory) or \
           (newNode.isDirectory and oldNode.isFile):
            raise TracError("Cannot view changes between directory and file")

        if newNode.isDirectory or oldNode.isDirectory:
            if oldNodePath.isRoot:
                oldQueryPath = u'//...%s' % oldNodePath.rev
            else:
                oldQueryPath = u'%s/...%s' % (oldNodePath.path,
                                             oldNodePath.rev)

            if newNodePath.isRoot:
                newQueryPath = u'//...%s' % newNodePath.rev
            else:
                newQueryPath = u'%s/...%s' % (newNodePath.path,
                                             newNodePath.rev)
        elif newNode.isFile or oldNode.isFile:
            oldQueryPath = oldNodePath.fullPath
            newQueryPath = newNodePath.fullPath
        else:
            raise TracError("Cannot diff two non-existant nodes")

        from p4trac.repos import _P4Diff2OutputConsumer
        output = _P4Diff2OutputConsumer(self._repos)

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
                yield (oldFileNode, newFileNode, Node.FILE, Changeset.EDIT)
            elif newFileNode:
                yield (oldFileNode, newFileNode, Node.FILE, Changeset.ADD)
            elif oldFileNode:
                yield (oldFileNode, newFileNode, Node.FILE, Changeset.DELETE)


class PerforceNode(Node):
    """A Perforce repository node (depot, directory or file)"""

    def __init__(self, nodePath, repos, log):
        log.debug('Created PerforceNode for %s' % nodePath.path)
        self._log = log
        self._repos = repos
        self._nodePath = nodePath
        self._node = self._repos.getNode(nodePath)
        node_type = self._get_kind()
        self.created_rev = self._node.change
        self.created_path = normalisePath(self._nodePath.path)
        self.rev = self.created_rev
        Node.__init__(self, self.created_path, self.rev, node_type)

    def _get_kind(self):
        if self._node.isDirectory:
            return Node.DIRECTORY
        elif self._node.isFile:
            return Node.FILE
        else:
            raise NoSuchNode(self._nodePath.path,
                             self._nodePath.rev)

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
        self._log.debug('PerforceNode.get_history(%r %s)' % (limit, self._nodePath.fullPath))
        if self._node.isFile:

            # Force population of the filelog history for efficiency
            from p4trac.repos import _P4FileLogOutputConsumer
            output = _P4FileLogOutputConsumer(self._repos)

            if limit is None:
                self._repos._connection.run(
                    'filelog',
                    '-i', '-l',
                    self._repos.fromUnicode(self._nodePath.fullPath),
                    output=output)
            else:
                self._repos._connection.run(
                    'filelog',
                    '-i', '-l',
                    '-m', str(limit),
                    self._repos.fromUnicode(self._nodePath.fullPath),
                    output=output)

            from p4trac.repos import NodePath

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
                            nodePath = NodePath(currentNode.nodePath.path,
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
                                NodePath(currentNode.nodePath.path,
                                         '#%i' % (currentNode.fileRevision-1)))
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
                            NodePath(currentNode.nodePath.path,
                                     '#%i' % (currentNode.fileRevision - 1)))
                    else:
                        currentNode = None

                i += 1

        elif self._node.isDirectory:
            
            # List all changelists that have affected this directory
            from p4trac.repos import _P4ChangesOutputConsumer
            output = _P4ChangesOutputConsumer(self._repos)

            if self._nodePath.isRoot:
                queryPath = '@<=%s' % self._nodePath.rev[1:]
            else:
                queryPath = '%s/...@<=%s' % (self._nodePath.path, self._nodePath.rev[1:])

            if limit is None:
                self._repos._connection.run(
                    'changes',
                    '-l', '-s', 'submitted',
                    self._repos.fromUnicode(queryPath),
                    output=output)
            else:
                self._repos._connection.run(
                    'changes',
                    '-l', '-s', 'submitted',
                    '-m', str(limit),
                    self._repos.fromUnicode(queryPath),
                    output=output)

            if output.errors:
                raise PerforceError(output.errors)
            
            changes = output.changes

            # And describe the contents of those changelists
            from p4trac.repos import _P4DescribeOutputConsumer
            output = _P4DescribeOutputConsumer(self._repos)
            self._repos._connection.run('describe', '-s',
                                        output=output,
                                        *[str(c) for c in changes])

            from p4trac.repos import NodePath

            for i in xrange(len(changes)):
                change = changes[i]
                nodePath = NodePath(self._nodePath.path, change)
                
                if i < len(changes)-1:
                    prevChange = changes[i+1]
                else:
                    prevChange = change-1

                prevNodePath = NodePath(self._nodePath.path, prevChange)

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

    def get_properties(self):
        self._log.debug('PerforceNode.get_properties')
        if self.kind is Node.FILE:
            props = {
                'type' : self._node.type
                }
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
                           self._changelist.user, self._changelist.time)

    def get_properties(self):
        self._log.debug('PerforceChangeset.get_properties()')
        import p4trac.repos
        try:
            results = self._repos._connection.run('fixes',
                                                  '-c', str(self._change))
            if results.errors:
                raise PerforceError(results.errors)

            fixes = ''
            print results.records
            for record in results.records:
                tktid = int(record['Job'][self._job_prefix_length:])
                fixes += '#%d ' % tktid

            if fixes != '':
                yield('Tickets', fixes, True, 'message')
        except p4trac.repos.NoSuchChangelist, e:
            raise NoSuchChangeset(e.change)

    def get_changes(self):
        self._log.debug('PerforceChangeset.get_changes()')
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
                        from p4trac.repos import NodePath
                        otherNode = self._repos.getNode(
                            NodePath(nodePath.path,
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
                from p4trac.repos import NodePath
                otherNodePath = NodePath(nodePath.path,
                                         '#%i' % (node.fileRevision - 1))
                otherNode = self._repos.getNode(otherNodePath)

                yield (normalisePath(nodePath.path),
                       Node.FILE,
                       Changeset.DELETE,
                       normalisePath(nodePath.path),
                       otherNode.change,
                       )
