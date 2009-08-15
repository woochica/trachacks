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
import sys

from trac.core import *
from trac.versioncontrol.web_ui import ChangesetModule
from trac.versioncontrol.web_ui.util import get_existing_node

from genshi.builder import tag

BRANCHES_PATH = 'branches'
TRUNK_PATH = 'trunk'
FILTER_NAME_PREFIX = 'branch_filter_'

python_version = tuple(sys.version_info[:2])
# If Python version is prior to 2.5, implement any
if python_version < (2, 5):
    def any(iterable):
        for member in iterable:
            if member:
                return True
        return False

def _unique_list(iterable):
    return list(set(iterable))

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
                if (change[0] and change[0].startswith(branch)) or (change[3] and change[3].startswith(branch))
               ]):
            return True
    return False

def _get_branch_name(branch_path, branches_path, trunk_path):
    if branch_path.startswith(trunk_path):
        return trunk_path

    # Get the branches dir name in case there's a sub-file in there
    return branch_path[len(branches_path):].strip(os.sep)

def _is_branch_path(change_path, branches_path):
    if change_path:
        return change_path.startswith(branches_path)
    else:
        return False

def _is_trunk_path(change_path, trunk_path):
    if change_path:
        return change_path.startswith(trunk_path)
    else:
        return False

def _conditional_add_branch_name(change_path, branches, branches_path, trunk_path):
    if _is_branch_path(change_path, branches_path):
        # Get only the path of the branch
        branch_name = _get_branch_name(change_path, branches_path, trunk_path)
        # branch_name now may include filenames in the branch, line 'branch2/file1'
        subfile_index = branch_name.find(os.sep)
        if subfile_index == -1:
            subfile_index = None
        branch_name = branch_name[:subfile_index]
        
        branches.append(os.path.join(branches_path, branch_name))
        
    if _is_trunk_path(change_path, trunk_path):
        branches.append(trunk_path)
            
def _get_changeset_branches(changeset_object, branches_path, trunk_path):
    branches = []
    for change in changeset_object.get_changes():
        _conditional_add_branch_name(change[0], branches, branches_path, trunk_path)
        _conditional_add_branch_name(change[3], branches, branches_path, trunk_path)
    return branches

def _get_changeset_event_branches(changeset_event, branches_path, trunk_path):
    branches = []
    for changeset_object in changeset_event[3][0]:
        branches += _get_changeset_branches(changeset_object, branches_path, trunk_path)
    return _unique_list(branches)
        
class BranchesTimelineModule(ChangesetModule):
    def __init__(self):
        self._branches_path = self._get_branches_path()
        self._trunk_path = self._get_trunk_path()
        self._filtered_branches = []

    def _get_configuration_path(self, variable_name, default_value):
        path = self.env.config.get('timeline-branches', variable_name)
        if path:
            path = path.strip(os.sep)
        else:
            path = default_value
        return path

    def _get_undisplayed_branches(self):
        branches = self.env.config.get('timeline-branches', 'undisplayed_branches', '')
        branches = branches.split(',')
        return [branch.strip() for branch in branches]
        
    def _get_branches_path(self):
        return self._get_configuration_path('branches_path', BRANCHES_PATH)

    def _get_trunk_path(self):
        return self._get_configuration_path('trunk_path', TRUNK_PATH)
    
    def _get_branches_names(self, req):
        # Find all branches and yield them
        repos = self.env.get_repository(req.authname)
        node = get_existing_node(req, repos, self._branches_path, repos.youngest_rev)
        undisplayed_branches = self._get_undisplayed_branches()
        for branch_node in node.get_entries():
            branch_name = _get_branch_name(branch_node.path, self._branches_path, self._trunk_path)
            # Branches are directories under the branches directory
            if node.isdir and (branch_name not in undisplayed_branches):
                yield branch_name
    
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

        # Save the filtered branches for the method render_timeline_event
        self._filtered_branches = filtered_branches
        
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

    def render_timeline_event(self, context, field, event):
        return_value = super(BranchesTimelineModule, self).render_timeline_event(context, field, event)
        
        if field != 'title':
            return return_value

        # Add the branches names to the title
        title = return_value
        branches = _get_changeset_event_branches(event, self._branches_path, self._trunk_path)

        branch_names = tag.cite(' in %s' % (', '.join(_get_branch_name(branch, self._branches_path, self._trunk_path)
                                                      for branch in branches))
                          )
        return title + branch_names
