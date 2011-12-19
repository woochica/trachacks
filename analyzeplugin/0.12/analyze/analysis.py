import re
from trac.core import *
from trac.ticket.model import Ticket
from trac.ticket.api import TicketSystem
from trac.config import ListOption, Option, ChoiceOption, BoolOption
from analyze.analyses import milestone, queue, rollup

class IAnalysis(Interface):
    """An extension point interface for adding analyses.  Each analysis
    can detect one or more issues in a report.  Each issue can suggest
    one or more solutions to the user.  The user can select amongst the
    solutions to fix the issue."""
    
    def can_analyze(self, report):
        """Return True if this analysis can analyze the given report."""
    
    def get_refresh_report(self):
        """Returns the report (and any params) to refresh upon making one or
        more fixes.  The default behavior is to refresh the current report."""
    
    def get_solutions(self, db, args, report):
        """Return a tuple of an issue description and a dict of its solution
        dict - or a list of solution dicts - with each dict comprising:
        
         * name - Text describing the solution
         * data - any serializable python object that defines the fix/solution
        
        Any "#<num>" ticket string found in the issue description or name
        will be converted to its corresponding href. 
        
        If data is a dict of field/value pairs of changes - or a list of
        these - then the base implementation of fix_issue() will execute
        the fix upon user command.  Use 'ticket' as the field name for the
        ticket's id value."""
    
    def fix_issue(self, db, data, author):
        """Execute the solution specified by the given data which was
        previously returned from get_solutions() above.  This method
        only needs to be defined if the data is not field/value pairs
        of changes or a list of these - i.e., the fix is more involved."""


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
    
    def can_analyze(self, report):
        """Returns True if this analysis can analyze the given report."""
        return True
    
    def get_refresh_report(self):
        """This default behavior refreshes the current report."""
        return None # default refreshes current report
    
    def get_solutions(self, db, args, report):
        raise Exception("Provide this method")
    
    def fix_issue(self, db, data, author):
        """This base fix updates a ticket with the field/value pairs in
        data.  The data object can either be a dict or a list of dicts
        with the 'ticket' field of each identifying the ticket to change."""
        if not isinstance(data,list):
            data = [data]
        
        # update each ticket
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

    def _isint(self, i):
        try:
            int(i)
        except (ValueError, TypeError):
            return False
        else:
            return True

    def _isnum(self, i):
        try:
            float(i)
        except (ValueError, TypeError):
            return False
        else:
            return True


class MilestoneDependencyAnalysis(Component, Analysis):
    """Building on mastertickets' blockedby relationships, this analyzes
    a report's tickets for one issue:
    
     1. Detects when dependent tickets are not scheduled in or before
        the master ticket's milestone. 
    
    This includes when dependent tickets are not yet scheduled or when
    the scheduled milestone has no due date.  Specify which reports can
    be analyzed with the milestone_reports option:
    
     [analyze]
     milestone_reports = 1,2
     on_change_clear = version
    
    In the example above, this analysis is only available for reports
    1 and 2.  Also, if a ticket's milestone gets fixed, then its version
    field will get cleared as defined by the on_change_clear option above.
    """
    
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
    """Building on mastertickets' blockedby relationships and the queue's
    position, this analyzes a report's tickets for two issues:
    
     1. Detects when dependent tickets are in the wrong queue.
     2. Detects when dependent tickets' positions are out of order.
    
    Specify which reports can be analyzed with the queue_reports option:
    
     [analyze]
     queue_reports = 1,2,3,9
    
    In the example above, this analysis is available for reports 1, 2, 3
    and 9.  If no queue_reports is provided, then the queue's full list of
    reports will be used instead from the [queues] 'reports' option.
    
    The queue_fields config option is the list of fields that define
    a queue.  You can optionally override with a report-specific option:
    
     [analyze]
     queue_fields = milestone,queue
     queue_fields.2 = queue
     queue_fields.9 = queue,phase!=verifying|readying
    
    In the example above, reports 1 and 3 are defined by fields 'milestone'
    and 'queue', report 2 is defined only by field 'queue', and report 9
    is defined by field 'queue' as well as filtering the 'phase' field.
    
    The filtering spec should usually match those in the report - i.e., via
    a pipe-delimited list specify which tickets to include ('=') or not
    include ('!=') in the analysis."""
    
    implements(IAnalysis)
    
    reports1 = ListOption('analyze', 'queue_reports', default=[],
            doc="Reports that can be queue dependency analyzed.")
    reports2 = ListOption('queues', 'reports', default=[],
            doc="Reports that can be queue dependency analyzed.")
    queue_fields = ListOption('analyze', 'queue_fields', default=[],
            doc="Ticket fields that define each queue.")
    audit = ChoiceOption('queues', 'audit', choices=['log','ticket','none'],
      doc="Record reorderings in log, in ticket, or not at all.")
    
    def can_analyze(self, report):
        # fallback to actual queue report list if not made explicit
        return report in (self.reports1 or self.reports2)
    
    def _add_args(self, args, report):
        """Split queue fields into standard and custom."""
        queue_fields = self.env.config.get('analyze','queue_fields.'+report,
                        self.queue_fields) # fallback if not report-specific
        if not isinstance(queue_fields,list):
            queue_fields = [f.strip() for f in queue_fields.split(',')]
        args['standard_fields'] = {}
        args['custom_fields'] = {}
        for name in queue_fields:
            vals = None
            if '=' in name:
                name,vals = name.split('=',1)
                not_ = name.endswith('!')
                if not_:
                    name = name[:-1]
                # save 'not' info at end of vals to pop off later
                vals = [v.strip() for v in vals.split('|')] + [not_]
            for field in TicketSystem(self.env).get_ticket_fields():
                if name == field['name']:
                    if 'custom' in field:
                        args['custom_fields'][name] = vals
                    else:
                        args['standard_fields'][name] = vals
                    break
            else:
                raise Exception("Unknown queue field: %s" % name)
    
    def get_solutions(self, db, args, report):
        if not args['col1_value1']:
            return '',[] # has no position so skip
        self._add_args(args, report)
        return queue.get_dependency_solutions(db, args)

    def fix_issue(self, db, data, author):
        """Honor queues audit config."""
        
        if not isinstance(data,list):
            data = [data]
        
        # find position field
        for k,v in data[0].items():
            if k == 'ticket':
                continue
            field = k
            if self.audit == 'ticket' or any(len(c) != 2 for c in data) or \
               not self._isint(v): # heuristic for position field
                return Analysis.fix_issue(self, db, data, author)
        
        # honor audit config
        cursor = db.cursor()
        for changes in data:
            id = changes['ticket']
            new_pos = changes[field]
            cursor.execute("""
                SELECT value from ticket_custom
                 WHERE name=%s AND ticket=%s
                """, (field,id))
            result = cursor.fetchone()
            if result:
                old_pos = result[0]
                cursor.execute("""
                    UPDATE ticket_custom SET value=%s
                     WHERE name=%s AND ticket=%s
                    """, (new_pos,field,id))
            else:
                old_pos = '(none)'
                cursor.execute("""
                    INSERT INTO ticket_custom (ticket,name,value)
                     VALUES (%s,%s,%s)
                    """, (id,field,new_pos))
            if self.audit == 'log':
                self.log.info("%s reordered ticket #%s's %s from %s to %s" \
                    % (author,id,field,old_pos,new_pos))
        db.commit()


class ProjectQueueAnalysis(QueueDependencyAnalysis):
    """This analysis builds on mastertickets' blockedby relationships under
    a parent-child semantics and the queue's position.  This analyzes a
    report's tickets for three issues:
    
     1. Detects when dependent tickets are in the wrong queue.
     2. Detects when dependent tickets have more than one parent.
     3. Detects when dependent tickets' positions are out of order.
    
    The last analysis above ensures that the relative ordering of two
    parents' children match the relative ordering of the parents.  To
    do this, then children can have only one parent (issue 2 above)
    else the algorithm will likely thrash.
    
    Specify which reports can be analyzed with the project_queue option:
    
     [analyze]
     project_reports = 12,14
    
    In the example above, this analysis is available for reports 12 and 14.
    To differentiate between peer relationships and parent-child
    relationships of blockedby tickets, parent tickets must have a
    unique ticket type that is specified in the project_type option (the
    default is 'epic'):
    
     [analyze]
     project_type = epic
     refresh_report = 2
    
    Tickets listed in project_reports should all be of this type.  If an
    'refresh_report' option is provided, then if there are fixes made,
    instead of refreshing the current report, it will load the impacted
    report.  You can also add parameters to that report if desired such as
    'impacted_report = 2?max=1000'.
    """
    
    implements(IAnalysis)
    
    reports = ListOption('analyze', 'project_reports', default=[],
            doc="Reports that can be queue dependency analyzed.")
    project_type = Option('analyze', 'project_type', default='epic',
            doc="Ticket type indicating a project (default is 'epic').")
    refresh_report = Option('analyze', 'project_refresh_report', default=None,
            doc="Report being impacted by this report.")
    
    @property
    def title(self):
        title = "%s Queue Analysis" % self._capitalize(self.project_type)
        return title
    
    @property
    def num(self):
        return 2 # analyze two adjacent projects
    
    def can_analyze(self, report):
        return report in self.reports
    
    def get_refresh_report(self):
        return self.refresh_report
    
    def get_solutions(self, db, args, report):
        if not args['col1_value1'] or not args['col1_value2']:
            return '',[] # has no position so skip
        self._add_args(args, report)
        args['project_type'] = self.project_type
        args['impacted_report'] = self.project_type
        return queue.get_project_solutions(db, args)


class ProjectRollupAnalysis(Component, Analysis):
    """This analysis builds on mastertickets' blockedby relationships under
    a parent-child semantics.  This analysis rolls up field values for each
    master ticket in a report.  Specify which reports can be analyzed with
    the rollup_reports option:
    
     [analyze]
     rollup_reports = 1,2,3,9
    
    In the example above, this analysis is available for reports 1, 2, 3
    and 9.  If no rollup_reports is provided, then the project_reports list
    is used instead.
    
    The available rollup stats are sum, min, max, median, mode, and a
    special 'pivot' analysis.  All but pivot apply to numeric fields, and
    all but sum apply to select option fields.  Here are several examples
    of specifying a stat for different fields:
    
     [analyze]
     rollup.effort = sum
     rollup.severity = min
     rollup.captain = mode
     rollup.phase = implementation
    
    In the example above, the project's
    
     * effort field sums all of its children numeric values
     * severity field gets set to the minimum (index) value of its children
     * captain field gets set to the most frequent captain of its children
     * phase pivots on the 'implementation' select option value value
    
    In brief, The pivot algorithm is as follows (using the option's index):
    
     * if all values are < the pivot value, then select their max value
     * else if all are > the pivot value, then select their min value
     * else select the pivot value
    """
    
    implements(IAnalysis)
    
    reports1 = ListOption('analyze', 'rollup_reports', default=[],
            doc="Reports that can be project rollup analyzed.")
    reports2 = ListOption('analyze', 'project_reports', default=[],
            doc="Reports that can be project rollup analyzed.")
    project_type = Option('analyze', 'project_type', default='epic',
            doc="Ticket type indicating a project (default is 'epic').")
    recurse = BoolOption('analyze', 'rollup_recurse', default=True,
            doc="Include all dependent tickets recursively in rollups.")
    
    @property
    def title(self):
        title = "%s Rollup Analysis" % self._capitalize(self.project_type)
        return title
    
    def can_analyze(self, report):
        # fallback to project report list if not made explicit
        return report in (self.reports1 or self.reports2)
    
    def _add_args(self, args, report):
        """Process rollup field configs."""
        args['standard_fields'] = {}
        args['custom_fields'] = {}
        for name,stat in self.env.config.options('analyze'):
            if not name.startswith('rollup.'):
                continue
            name = name[7:]
            rollup = {'stat':stat.strip()}
            for field in TicketSystem(self.env).get_ticket_fields():
                if name == field['name']:
                    rollup['options'] = field.get('options',None)
                    rollup['numeric'] = True
                    if rollup['options']:
                        # check if all options are numeric
                        for option in rollup['options']:
                            if not self._isnum(option):
                                rollup['numeric'] = False
                                break
                    if 'custom' in field:
                        args['custom_fields'][name] = rollup
                    else:
                        args['standard_fields'][name] = rollup
                    break
            else:
                raise Exception("Unknown rollup field: %s" % name)
    
    def get_solutions(self, db, args, report):
        self._add_args(args, report)
        if not args['standard_fields'] and not args['custom_fields']:
            return '',[] # has rollup fields so skip
        args['project_type'] = self.project_type
        args['recurse'] = self.recurse
        return rollup.get_solutions(db, args)
