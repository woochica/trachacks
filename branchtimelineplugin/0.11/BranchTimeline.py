"""
The BranchTimeline plugin changes the behaviour of the timeline and enables you to view changes of a specific branch/trunk.

Requirements:
   - Trac 0.11.
   - Subversion repository.

Installation:
   - Put the python file in the plugins directory of the trac environment (or in the global plugins directory).
   - Components changes:
      - Disable the basic trac component ChangesetModule.
      - Enable the component BranchesTimelineModule.
      - These changes can be done via the WebAdmin interface or by adding the following lines to trac.ini:
[components]
trac.versioncontrol.web_ui.changeset.changesetmodule = disabled
BranchTimeline.* = enabled

Configuration:
   - The following configuration can be added to trac.ini:
[timeline-branches]
branches_path = branches
trunk_path = trunk
"""

import os.path

from trac.core import *
from trac.versioncontrol.web_ui import ChangesetModule
from trac.versioncontrol.web_ui.util import get_existing_node

BRANCHES_PATH = 'branches'
TRUNK_PATH = 'trunk'
FILTER_NAME_PREFIX = 'branch_filter_'

def _get_filter_name(branch_name):
    return "%s%s" % (FILTER_NAME_PREFIX, branch_name)

def _get_branch_path(filter_name, branches_path):
    return os.path.join(branches_path, filter_name[len(FILTER_NAME_PREFIX):])

def _get_filtered_branches(filters, branches_path):
    branches = []
    for timeline_filter in filters:
        if timeline_filter.startswith(FILTER_NAME_PREFIX):
            branches.append(_get_branch_path(timeline_filter, branches_path))
    return branches

def _changeset_belongs_to_branches(changeset_object, branches):
    for change in changeset_object.get_changes():
        # Check if any of the branches appear in the change
        if any([True
                for branch in branches
                # Again, use of indices...
                if (change[0] and branch in change[0]) or (change[3] and branch in change[3])
               ]):
            return True
    return False

class BranchesTimelineModule(ChangesetModule):
    def __init__(self):
        self._branches_path = self._get_branches_path()
        self._trunk_path = self._get_trunk_path()

    def _get_configuration_path(self, variable_name, default_value):
        path = self.env.config.get('timeline-branches', variable_name)
        if path:
            path = path.strip(os.sep)
        else:
            path = default_value
        return path
        
    def _get_branches_path(self):
        return self._get_configuration_path('branches_path', BRANCHES_PATH)

    def _get_trunk_path(self):
        return self._get_configuration_path('trunk_path', TRUNK_PATH)
    
    def _get_branches_names(self, req):
        # Find all branches and yield them
        repos = self.env.get_repository(req.authname)
        node = get_existing_node(req, repos, self._branches_path, repos.youngest_rev)
        branches_directory_length = len(self._branches_path) # Optimization (although I never checked if that's slow)
        for branch_node in node.get_entries():
            # Branches are directories under the branches directory
            if node.isdir:
                yield branch_node.path[branches_directory_length:].strip(os.sep)
    
    def get_timeline_filters(self, req):
        """Return a list of filters that this event provider supports.
        
        Each filter must be a (name, label) tuple, where `name` is the internal
        name, and `label` is a human-readable name for display.

        Optionally, the tuple can contain a third element, `checked`.
        If `checked` is omitted or True, the filter is active by default,
        otherwise it will be inactive.
        """
        # Superior (ordinary) filters
        for timeline_filter in super(BranchesTimelineModule, self).get_timeline_filters(req):
            yield timeline_filter

        # Trunk filter
        yield ('trunk', 'Trunk checkins', True)

        # Branches filters
        for branch_name in self._get_branches_names(req):
            filter_name = _get_filter_name(branch_name)
            yield (filter_name, 'Branch %s checkins' % (branch_name, ), True)

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
        # filtered_branches are the branches that we DO want to see...
        filtered_branches = _get_filtered_branches(filters, self._branches_path)

        # Trunk filter
        if 'trunk' in filters:
            filtered_branches.append(self._trunk_path)

        changesets_iterator = super(BranchesTimelineModule, self).get_timeline_events(req, start, stop, filters)

        # Go over each change in each changeset and check if it belongs to one of the branches
        for changeset in changesets_iterator:
            # Unfortunately, Trac isn't written so well, and so here we must use indices.
            for changeset_object in changeset[3][0]:
                if _changeset_belongs_to_branches(changeset_object, filtered_branches):
                    yield changeset
