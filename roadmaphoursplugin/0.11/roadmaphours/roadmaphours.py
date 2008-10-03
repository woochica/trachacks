"""
RoadmapHours:
Provides alternate group stats provider RoadmapHoursTicketGroupStatsPlugin
for Trac 0.11.

Configuration in trac.ini:
[roadmaphours]
# Number of hours assumed for tickets with less than 0.25 estimated hours.
assumed_estimate = 6
# Number of additional hours assumed for tickets that have gone over
# their estimate.
additional_hours = 4
"""

# TODO: Make assumed number of hours for no estimate configurable

from datetime import datetime
import re

from trac.config import IntOption
from trac.core import *
from trac.ticket.roadmap import *
from trac.ticket import Ticket

class RoadmapHoursTicketGroupStatsProvider(Component):
    """Ticket group stats provider for TimingAndEstimationPlugin."""

    implements(ITicketGroupStatsProvider)

    assumed_estimate = IntOption('roadmaphours', 'assumed_estimate',
	    6,
	    """Estimated hours value used for tickets with <0.1 estimated hours.""")
    additional_hours = IntOption('roadmaphours', 'additional_hours',
	    4,
	    """Number of additional hours assumed needed for tickets that
	    have gone over their estimates.""")

    def _get_ticket_groups(self):
        """Returns a list of dict describing the ticket groups
        in the expected order of appearance in the milestone progress bars.
        """
        if 'milestone-groups' in self.config:
            groups = {}
            order = 0
            for groupname, value in self.config.options('milestone-groups'):
                qualifier = 'status'
                if '.' in groupname:
                    groupname, qualifier = groupname.split('.', 1)
                group = groups.setdefault(groupname, {'name': groupname,
                                                      'order': order})
                group[qualifier] = value
                order = max(order, int(group['order'])) + 1
            return [group for group in sorted(groups.values(),
                                              key=lambda g: int(g['order']))]
        else:
            return self.default_milestone_groups

    def get_ticket_group_stats(self, ticket_ids):
        total_cnt = len(ticket_ids)
        all_statuses = set(TicketSystem(self.env).get_all_status())
	worked_hours = 0.0
	expected_hours = 0.0
        if total_cnt:
            cursor = self.env.get_db_cnx().cursor()
            str_ids = [str(x) for x in sorted(ticket_ids)]
	    cursor.execute("SELECT status, est.value as 'Est', "
			   "act.value as 'Act' "
			   "FROM ticket t "
			   "LEFT OUTER JOIN ticket_custom est ON "
			   "  (t.id=est.ticket AND est.name='estimatedhours') "
			   "LEFT OUTER JOIN ticket_custom act ON "
			   "  (t.id=act.ticket AND act.name='totalhours') "
			   "WHERE t.id IN (%s)" %
			   ",".join(str_ids))
	    for status, est, act in cursor:
		if act:
		    act = float(act)
		    if status == 'closed':
			expected_hours += act
			worked_hours += act
		    else:
			est = float(est)
			if est < 0.1:
			    # Assume about a day's work
			    est = self.assumed_estimate
			if est > act:
			    expected_hours += est
			else:
			    # Assume about half a day more
			    expected_hours += act + self.additional_hours
			worked_hours += act

        stat = TicketGroupStats('ticket status', 'hour')
	query_cols = ["summary", "owner", "type", "priority",
		      "component", "estimatedhours", "totalhours"]
	stat.qry_args = {"col" : query_cols}
	query_args = {}
	query_args.setdefault('col', query_cols)
	query_args.setdefault('status', []).append('closed')
	stat.add_interval("Worked",
			  int(round(worked_hours)), query_args,
			  'closed', True);
	query_args = {"status" : [s for s in all_statuses if s != 'closed']}
	query_args.setdefault('col', query_cols)
	stat.add_interval("Remaining",
			  int(round(expected_hours - worked_hours)), query_args,
			  'open', False);
        stat.refresh_calcs()
        return stat
