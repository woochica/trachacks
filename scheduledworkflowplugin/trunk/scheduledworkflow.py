"""
ScheduledWorkflowPlugin : a plugin for Trac, http://trac.edgewall.org
"""

from trac.core import *
from trac.ticket.model import Ticket
from datetime import datetime
from trac.util.datefmt import format_datetime, from_utimestamp, \
                              to_utimestamp, utc
from trac.admin import IAdminCommandProvider
from trac.util.text import print_table, printout
from trac.ticket.api import TicketSystem
import time

class ScheduledWorkflow(Component):
    """
    Automatically transition all tickets that have been in a given
    state for a certain period of time.

    This plugin provides a new subcommand for trac-admin that makes it
    easy to automatically transition tickets after a certain period of
    time.

    You might want to consider invoking it from a cronjob.
    """
    
    implements(IAdminCommandProvider)

    common_days = ['2', '3', '7', '14', '30']

    # IAdminCommandProvider methods

    def get_admin_commands(self):
        yield ('transition', '<oldstate> <newstate> <days> [<user> <explanation>]',
               'Transition tickets from <oldstate> to <newstate> if they have been in <oldstate> for <days> or longer',
               self._complete_transition, self._do_transition)
        yield ('transition_list', '<oldstate> <days>',
               'List tickets that have been in <oldstate> for <days> or longer',
               self._complete_transition_list, self._list_transition)

    def _do_transition(self, oldstate, newstate, days, user=None, explanation=None):
        tc = 0
        for t in self._get_tickets(oldstate, days):
            t['status'] = newstate
            t.save_changes(user, explanation)
            tc += 1
        print("Transitioned %d tickets from %s to %s"%(tc, oldstate, newstate))

    def _list_transition(self, oldstate, days):
        for t in self._get_tickets(oldstate, days):
            print("%d: %s (%s)" % (t.id, t['summary'], t['status']))

    def _get_tickets(self, oldstate, days):
        db = self.env.get_db_cnx()
        timecutoff = (int(time.time()) - float(days) * 86400) * 1000000
        cursor = db.cursor() 
        cursor.execute('''
                        SELECT id FROM ticket LEFT JOIN ticket_change ON (id = ticket AND field = %s) WHERE ticket.status = %s GROUP BY ticket.id
                        HAVING MAX(ticket_change.time) <= %s OR (MAX(ticket_change.time) IS NULL AND MAX(ticket.time) <= %s) ORDER BY id
                       ''', ('status', oldstate, timecutoff, timecutoff))
        for (a,) in cursor:
            yield Ticket(self.env, a)

    def _complete_transition(self, args):
        if len(args) < 3:
            states = TicketSystem(self.env).get_all_status()
            if len(args) == 2 and args[0] in states:
                states.remove(args[0])
            return states
        if len(args) == 3:
            return self.common_days
        if len(args) == 4:
            return self._get_user_list()
        if len(args) == 5:
            return self._get_explanations(args[3])

    def _complete_transition_list(self, args):
        if len(args) == 1:
            return TicketSystem(self.env).get_all_status()
        if len(args) == 2:
            return self.common_days

    def _get_user_list(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor() 
        cursor.execute("SELECT DISTINCT author FROM ticket_change")
        for (a,) in cursor:
            yield a

    def _get_explanations(self, author):
        db = self.env.get_db_cnx()
        cursor = db.cursor() 
        cursor.execute("SELECT DISTINCT newvalue FROM ticket_change WHERE field = %s AND author = %s AND newvalue IS NOT NULL", ('comment', author))
        for (a,) in cursor:
            yield a
