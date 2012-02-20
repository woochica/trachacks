"""
SensitiveTicketsPlugin : a plugin for Trac, http://trac.edgewall.org

Based on the example vulnerability_tickets plugin, but SensitivityTickets uses a checkbox to control status versus text.

See: http://trac.edgewall.org/browser/trunk/sample-plugins/permissions/vulnerability_tickets.py
"""

from trac.core import *
from trac.config import BoolOption
from trac.perm import IPermissionPolicy, IPermissionRequestor
from trac.env import IEnvironmentSetupParticipant
from trac.ticket.model import Ticket
from trac.ticket.api import ITicketManipulator
from trac.timeline.api import ITimelineEventProvider
from trac.resource import ResourceNotFound
from datetime import datetime
from trac.util.datefmt import format_datetime, from_utimestamp, \
                              to_utimestamp, utc
from trac.util import as_bool

class SensitiveTicketsPolicy(Component):
    """Prevent public access to security sensitive tickets.
    
    Add the SENSITIVE_VIEW permission as a pre-requisite for any
    other permission check done on tickets that have been marked (through
    the UI) as "Sensitive".

    Once this plugin is enabled, you'll have to insert it at the appropriate
    place in your list of permission policies, e.g.
    {{{
    [trac]
    permission_policies = SensitiveTicketsPolicy, AuthzPolicy, 
                          DefaultPermissionPolicy, LegacyAttachmentPolicy
    }}}

    This plugin also adds the REDACTED_SENSITIVE_ACTIVITY_VIEW
    permission.  Accounts with this permission will be able to see
    activity on sensitive material in the timeline, but will only be
    able to identify it by ticket number, comment number, and
    timestamp.
    
    REDACTED_SENSITIVE_ACTIVITY_VIEW can be useful (for example) for
    providing a notification daemon the ability to tell that some
    activity happened without leaking the content of that activity.
    """
    
    implements(IPermissionPolicy, IPermissionRequestor, IEnvironmentSetupParticipant, ITicketManipulator, ITimelineEventProvider)

    allow_reporter = BoolOption('sensitivetickets', 'allow_reporter', 'false',
                                '''Whether the reporter of a sensitive
ticket should have access to that ticket even if they do not have
SENSITIVE_VIEW privileges''')

    allow_cc = BoolOption('sensitivetickets', 'allow_cc', 'false',
                          '''Whether users listed in the cc field of a
sensitive ticket should have access to that ticket even if they do not
have SENSITIVE_VIEW privileges''')

    allow_owner = BoolOption('sensitivetickets', 'allow_owner', 'true',
                             '''Whether the owner of a sensitive
ticket should have access to that ticket even if they do not have
SENSITIVE_VIEW privileges''')

    limit_sensitivity = BoolOption('sensitivetickets', 'limit_sensitivity', 'false',
                                    '''With limit_sensitivity set to
true, users cannot set the sensitivity checkbox on a ticket unless
they are authenticated and would otherwise be permitted to deal with
the ticket if it were marked sensitive.

This prevents users from marking the tickets of other users as "sensitive".''')

    # IPermissionPolicy methods

    def check_permission(self, action, username, resource, perm):
        # We add the 'SENSITIVE_VIEW' pre-requisite for any action
        # other than 'SENSITIVE_VIEW' itself, as this would lead
        # to recursion.
        if action == 'SENSITIVE_VIEW':
            return
        
        # Check whether we're dealing with a ticket resource
        while resource:
            if resource.realm == 'ticket':
                break
            resource = resource.parent

        if resource and resource.realm == 'ticket' and resource.id is not None:
            bypass = False
            try:
                ticket = Ticket(self.env, int(resource.id))
                sensitive = ticket['sensitive']
                if as_bool(sensitive):
                    bypass = self.bypass_sensitive_view(ticket, username)
            except ResourceNotFound:
                sensitive = 1  # Fail safe to prevent a race condition.

            if as_bool(sensitive):
                if 'SENSITIVE_VIEW' not in perm and not bypass:
                    return False

    # IPermissionRequestor methods

    def get_permission_actions(self):
        yield 'SENSITIVE_VIEW'
        yield 'REDACTED_SENSITIVE_ACTIVITY_VIEW'

    # ITicketManipulator methods:
    def validate_ticket(self, req, ticket):
        if not self.limit_sensitivity:
            return []
        sensitive = 1
        try:
            sensitive = ticket['sensitive']
        except:
            pass
        if as_bool(sensitive):
            if req.authname is 'anonymous':
                return [(None, 'Sorry, you cannot create or update a sensitive ticket without at least logging in first')]
            if self.bypass_sensitive_view(ticket, req.authname):
                return []
            req.perm(ticket.resource).require('SENSITIVE_VIEW')
        return []


    ### methods for IEnvironmentSetupParticipant

    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""

    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)


    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.
        """
        return 'sensitive' not in self.config['ticket-custom']
            

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        if not self.environment_needs_upgrade(db):
            return

        custom = self.config['ticket-custom']

        custom.set('sensitive','checkbox')
        custom.set('sensitive.label', "Sensitive")
        custom.set('sensitive.value', '0')

        self.config.save()

    ### ITimelineEventProvider methods:
    def get_timeline_filters(self, req):
        if ('REDACTED_SENSITIVE_ACTIVITY_VIEW' in req.perm and
            'SENSITIVE_VIEW' not in req.perm):
            yield ('redacted_timeline_events', 'Activity on sensitive tickets', False)

    def get_timeline_events(self, req, start, stop, filters):
        if ('redacted_timeline_events' in filters and
            'REDACTED_SENSITIVE_ACTIVITY_VIEW' in req.perm and
            'SENSITIVE_VIEW' not in req.perm):
            ts_start = to_utimestamp(start)
            ts_stop = to_utimestamp(stop)

            db = self.env.get_db_cnx()
            cursor = db.cursor()

            if 'ticket_details' in filters:
                # only show sensitive ticket changes (edits, closure) if the 'ticket_details' filter is on:
                cursor.execute("""
                    SELECT DISTINCT t.id,tc.time,tc.oldvalue
                    FROM ticket_change tc 
                        INNER JOIN ticket t ON t.id = tc.ticket 
                            AND tc.time >= %s AND tc.time <= %s  AND tc.field = %s
                        INNER JOIN ticket_custom td ON t.id = td.ticket
                            AND td.name = %s AND td.value = %s
                    ORDER BY tc.time
                    """, (ts_start, ts_stop, 'comment', 'sensitive', '1'))
                for tid,t,cid in cursor:
                    yield ('sensitive_activity', from_utimestamp(t), 'redacted', (tid, cid))
            # always show new sensitive tickets:
            cursor.execute('''
               SELECT DISTINCT id, time FROM
                  ticket t INNER JOIN ticket_custom tc ON t.id = tc.ticket
                   AND t.time >= %s AND t.time <= %s
                   AND tc.name = %s AND tc.value = %s
               ORDER BY time
               ''', (ts_start, ts_stop, 'sensitive', '1'))
            for tid,t in cursor:
                yield ('sensitive_activity', from_utimestamp(t), 'redacted', (tid, None))

    def render_timeline_event(self, context, field, event):
        tid, cid = event[3]
        if field == 'title':
            return 'Sensitive Activity'
        elif field == 'description':
            return '[REDACTED]'
        elif field == 'url':
            href = context.href.ticket(tid)
            if cid:
                href += '#comment:' + str(cid)
            return href


    ### private methods:
        
    def bypass_sensitive_view(self, ticket, username):
        '''Returns whether the sensitivetickets permission allows a
        bypass of the SENSITIVE_VIEW setting for a given ticket
        '''
        if username == 'anonymous':
            return False
        return (self.allow_owner and (ticket['owner'] == username)) or \
            (self.allow_reporter and (ticket['reporter'] == username)) or \
            (self.allow_cc and (username in [x.strip() for x in ticket['cc'].split(',')]))
