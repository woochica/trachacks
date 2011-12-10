import re
from trac.core import *
from trac.ticket.model import Ticket
from trac.ticket.api import TicketSystem
from trac.config import ListOption, Option
from analyze.analyses import milestone, queue

class IAnalysis(Interface):
    """An extension point interface for adding analyses."""
    
    def get_solutions(self, db, args, report):
        """Return a list of solution dicts comprising:
        
         * name - Text describing the solution
         * data - dict of data to use for the fix
        """
    def fix_issue(self, db, data):
        """Execute the solution specified by the given data."""
       

class Analysis(object):
    """Abstract class for common analysis properties and utilities."""
    
    @property
    def path(self):
        """Returns the analysis instance's unique path name."""
        return self.__class__.__name__.lower()
    
    @property
    def num(self):
        """Returns the number of adjacent tickets needed for analysis."""
        return 1
    
    @property
    def title(self):
        """Returns the analysis class' title used for display purposes.
        This default implementation returns the analysis's class name
        with any camel case split into words."""
        # split CamelCase to Camel Case
        return self._split_camel_case(self.__class__.__name__)
    
    @property
    def desc(self):
        """Returns the analysis description.  The default implementation
        returns the first paragraph of the docstring."""
        return self.__doc__.split('\n')[0]
    
    def can_analyze(self, report):
        """Returns True if this analysis can analyze the given report."""
        return True
    
    def fix_issue(self, db, data, author):
        """Base fix is to update a ticket with the data values which can
        either be a dict of changes or a list of such dicts."""
        if not isinstance(data,list):
            data = [data]
        
        # update each ticket - TODO: honor queues audit config
        for changes in data:
            ticket = Ticket(self.env, changes['ticket'])
            del changes['ticket']
            ticket.populate(changes)
            ticket.save_changes(author=author, comment='')
        return None
    
    # private methods
    def _capitalize(self, word):
        if len(word) <= 1:
            return word.upper()
        return word[0].upper() + word[1:]
    
    def _split_camel_case(self, s):
        return re.sub('((?=[A-Z][a-z])|(?<=[a-z])(?=[A-Z]))', ' ', s).strip()


class MilestoneDependencyAnalysis(Component, Analysis):
    """Dependent tickets are in milestones after #'s milestone.
    This builds on mastertickets' blockedby relationships.
    No blockedby ticket should be in a later milestone than
    this ticket."""
    
    implements(IAnalysis)
    
    reports = ListOption('analyze', 'milestone_reports', default=[],
            doc="Reports that can be milestone dependency analyzed.")
    on_change_clear = ListOption('analyze', 'on_change_clear', default=[],
            doc="Ticket fields to clear on change of milestone.")
    
    def can_analyze(self, report):
        return report in self.reports
    
    def get_solutions(self, db, args, report):
        args['on_change_clear'] = self.on_change_clear
        return milestone.get_dependency_solutions(db, args)


class QueueDependencyAnalysis(Component, Analysis):
    """Dependent tickets are not in the queue or are after #.
    This builds on mastertickets' blockedby relationships and
    the queue's position.  No blockedby ticket should be lower
    in the queue (i.e., have a larger position number) than
    this ticket."""
    
    implements(IAnalysis)
    
    reports1 = ListOption('analyze', 'queue_reports', default=[],
            doc="Reports that can be queue dependency analyzed.")
    reports2 = ListOption('queues', 'reports', default=[],
            doc="Reports that can be queue dependency analyzed.")
    queue_fields = ListOption('analyze', 'queue_fields', default=[],
            doc="Ticket fields that define each queue.")
    
    def can_analyze(self, report):
        # fallback to actual queue report list if not made explicit
        return report in (self.reports1 or self.reports2)
    
    def _add_args(self, args, report):
        """Adds several args needed for solution processing."""
        # split the queue fields for this report into standard and custom
        queue_fields = self.env.config.get('analyze','queue_fields.'+report,
                        self.queue_fields) # fallback if not report-specific
        if not isinstance(queue_fields,list):
            queue_fields = [f.strip() for f in queue_fields.split(',')]
        args['standard_fields'] = []
        args['custom_fields'] = []
        for name in queue_fields:
            for field in TicketSystem(self.env).get_ticket_fields():
                if name == field['name']:
                    if 'custom' in field:
                        args['custom_fields'].append(name)
                    else:
                        args['standard_fields'].append(name)
                    break
            else:
                raise Exception("Unknown queue field: %s" % name)
    
    def get_solutions(self, db, args, report):
        if not args['col1_value1']:
            return [] # has no position so skip
        self._add_args(args, report)
        return queue.get_dependency_solutions(db, args)


class ProjectQueueAnalysis(QueueDependencyAnalysis):
    """#'s sub-tickets are not in the queue or are after #'s.
    This builds on mastertickets' blockedby relationships using
    *containment* (i.e., parent-child) semantics, and also the
    queue's position.  All sub-tickets of the first project
    should be ordered before all sub-tickets of the second
    project, and so on."""
    
    implements(IAnalysis)
    
    reports = ListOption('analyze', 'project_reports', default=[],
            doc="Reports that can be queue dependency analyzed.")
    project_type = Option('analyze', 'project_type', default='epic',
            doc="Ticket type indicating a project (aka epic).")
    
    @property
    def title(self):
        title = "%s Queue Analysis" % self._capitalize(self.project_type)
        return title
    
    @property
    def desc(self):
        name = self._capitalize(self.project_type)
        return "%s %s" % (name,self.__doc__.split('\n')[0])
    
    @property
    def num(self):
        return 2 # analyze two adjacent projects
    
    def can_analyze(self, report):
        return report in self.reports
    
    def get_solutions(self, db, args, report):
        if not args['col1_value1'] or not args['col1_value2']:
            return [] # has no position so skip
        self._add_args(args, report)
        args['project_type'] = self.project_type
        return queue.get_project_solutions(db, args)
