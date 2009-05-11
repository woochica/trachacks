"""
The TimelineCheckinFilter plugin changes the behaviour of the timeline and enables you to view changes to particular paths, or by particular users.

Based on BranchTimelinePlugin

Requirements:
   - Trac 0.11.
   - Subversion repository.

Installation:
   - Put the python file in the plugins directory of the trac environment (or in the global plugins directory).
   - Components changes:
      - Disable the basic trac component ChangesetModule.
      - Enable the component TimelineCheckinFilter
      - These changes can be done via the WebAdmin interface or by adding the following lines to trac.ini:
[components]
trac.versioncontrol.web_ui.changeset.changesetmodule = disabled
TimelineCheckinFilter.* = enabled

Configuration:
   - The following configuration can be added to trac.ini:
[timeline-checkin-filter]
filter_paths = trunk:trunk, branch1:branches/branch1, proj2-trunk:project2/trunk, arbitrary-label:arbitrary/path
filter_users = username1, username2

"""

import os.path
import sys
import logging

from trac.core import *
from trac.versioncontrol.web_ui import ChangesetModule
from trac.versioncontrol.web_ui.util import get_existing_node

FILTER_PATH_NAME_PREFIX = 'path_filter_'
FILTER_USER_NAME_PREFIX = 'user_filter_'

python_version = tuple(sys.version_info[:2])
# If Python version is prior to 2.5, implement any
if python_version < (2, 5):
    def any(iterable):
        for member in iterable:
            if member:
                return True
        return False
    
def _get_filtered_paths(filters, path_lookup):
    paths = []
    for timeline_filter in filters:
        if timeline_filter.startswith(FILTER_PATH_NAME_PREFIX):
            paths.append(path_lookup[timeline_filter[len(FILTER_PATH_NAME_PREFIX):]])
    return paths

def _get_filtered_users(filters):
    users = []
    for timeline_filter in filters:
        if timeline_filter.startswith(FILTER_USER_NAME_PREFIX):
            users.append(timeline_filter[len(FILTER_USER_NAME_PREFIX):])
    return users

def _changeset_belongs_to_paths(changeset_object, paths):
    for change in changeset_object.get_changes():
        # Check if any of the paths appear in the change
        if any([True
                for path in paths
                # Again, use of indices...
                if (change[0] and path in change[0]) or \
                    (change[2] and change[2]=='copy' and change[3] and path in change[3])
               ]):
            return True
    return False

def sort(s):
    """Return a sorted copy of s"""
    n = s
    n.sort()
    return n

class TimelineCheckinFilterModule(ChangesetModule):
    def __init__(self):
        self._filter_paths = {}
        self._filter_users = []
        display = self.env.config.get('timeline-checkin-filter', 'filter_paths', '')
        display = display.strip()
        display = display.split(',')
        for path in display:
            path = path.strip()
            path = path.split(':')
            label = path[0]
            path = path[1]
            if path:
                path = path.strip(os.sep)
            self._filter_paths[label] = path
        users = self.env.config.get('timeline-checkin-filter', 'filter_users', '')
        users = users.split(',')
        for user in users:
            user = user.strip()
            self._filter_users.append(user)

    def get_timeline_filters(self, req):
        """Return a list of filters that this event provider supports.
        
        Each filter must be a (name, label) tuple, where `name` is the internal
        name, and `label` is a human-readable name for display.

        Optionally, the tuple can contain a third element, `checked`.
        If `checked` is omitted or True, the filter is active by default,
        otherwise it will be inactive.
        """
        # Superior (ordinary) filters
        for timeline_filter in super(TimelineCheckinFilterModule, self).get_timeline_filters(req):
            yield timeline_filter

        # Paths filters
        for path_name in sort(self._filter_paths.keys()):
            filter_name = "%s%s" % (FILTER_PATH_NAME_PREFIX, path_name)
            yield (filter_name, 'Checkins to %s' % (path_name, ), True)

        # User filters
        for user in self._filter_users:
            filter_name = "%s%s" % (FILTER_USER_NAME_PREFIX, user)
            yield (filter_name, 'Checkins by %s' % (user,), True)

    def get_timeline_events(self, req, start, stop, filters):
        """Return a list of events in the time range given by the `start` and
        `stop` parameters.

        The `filters` parameters is a list of the enabled filters, each item
        being the name of the tuples returned by `get_timeline_filters`.

        Since 0.11, the events are `(kind, date, author, data)` tuples,
        where `kind` is a string used for categorizing the event, `date`
        is a `datetime` object, `author` is a string and `data` is some
        private data that the component will reuse when rendering the event.

        When the event has been created indirectly by another module,
        like this happens when calling `AttachmentModule.get_timeline_events()`
        the tuple can also specify explicitly the provider by returning tuples
        of the following form: `(kind, date, author, data, provider)`.

        Before version 0.11,  the events returned by this function used to
        be tuples of the form `(kind, href, title, date, author, markup)`.
        This is still supported but less flexible, as `href`, `title` and
        `markup` are not context dependent.
        """
        # filtered_paths are the paths that we DO want to see...
        filtered_paths = _get_filtered_paths(filters, self._filter_paths)

        filtered_users = _get_filtered_users(filters)

        changesets_iterator = super(TimelineCheckinFilterModule, self).get_timeline_events(req, start, stop, filters)

        # Go over each change in each changeset and check if it belongs to one of the paths
        for changeset in changesets_iterator:
            # Unfortunately, Trac isn't written so well, and so here we must use indices.
            if (not filtered_users) or (changeset[2] and changeset[2] in filtered_users):
                for changeset_object in changeset[3][0]:
                    if (not filtered_paths) or _changeset_belongs_to_paths(changeset_object, filtered_paths):
                        yield changeset
