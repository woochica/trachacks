# 
# Synchronises tickets in trac with tasks in SlimTimer
#

import re
import os
from string import lower

from trac.core import *
from trac.ticket.api import ITicketChangeListener
from trac.ticket.model import Ticket

import slimtimer as ST
from users import Users
from trac_ticket import TracTicket

#
# Ahh, I don't know Python. Surely there's a safer way of doing parseInt than
# this.
#
def getint(str):
    try:
        rv = int(str)
    except ValueError:
        rv = -1
    return rv

def getfloat(str):
    try:
        rv = float(str)
    except ValueError:
        rv = -1
    return rv

#
# The ticket change listener
#
class TracSlimTimerTicketChangeListener(Component):

    implements(ITicketChangeListener)

    #
    # ITicketChangeListener methods
    #

    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        pass

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified.
        
        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """
        
        if not ticket.values.get('status'):
            return

        new_status     = ticket['status']
        status_changed = old_values.get('status') != None

        if status_changed:
            if new_status == 'assigned':
                self.log.debug('Ticket assigned: %s' % 
                               ticket.values.get('summary'))
                self._do_ticket_assigned(ticket, old_values, author)

            elif new_status == 'reopened':
                self.log.debug('Ticket re-opened: %s' % 
                               ticket.values.get('summary'))
                self._do_ticket_reopened(ticket, old_values, author)

            elif new_status == 'closed':
                self.log.debug('Ticket closed: %s' % 
                               ticket.values.get('summary'))
                self._do_ticket_closed(ticket, old_values, author)

        elif new_status == 'assigned' or new_status=='reopened':
            self._do_ticket_updated(ticket, old_values, author)

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        if ticket.values.get('status','') in ('assigned', 'reopened'):
            self.log.debug('Ticket deleted: %s' % ticket.values.get('summary'))
            self._do_ticket_deleted(ticket)

    # 
    # Implementation helpers
    #

    def _do_ticket_assigned(self, ticket, old_values, author):
        """
        A ticket has been accepted. Create and update task as necessary.
        """

        st_task = self._get_task(ticket, create = True,
                                 old_values = old_values)
        if not st_task:
            return

        st_task.complete = False

        self.log.debug("Creating task: %s" % st_task.name)
        self._sync_task(st_task, ticket, old_values, author)

    def _do_ticket_reopened(self, ticket, old_values, author):
        """
        A ticket has been re-opened. Update the task or create it if necessary.
        """

        st_task = self._get_task(ticket, create = True,
                                 old_values = old_values)
        if not st_task:
            return

        st_task.complete = False

        self.log.debug("Re-opening task: %s" % st_task.name)
        self._sync_task(st_task, ticket, old_values, author)

    def _do_ticket_closed(self, ticket, old_values, author):
        """
        A ticket has been closed. Mark the task as complete.
        """

        st_task = self._get_task(ticket, create = False,
                                 old_values = old_values)
        if not st_task:
            return

        st_task.complete = True

        self.log.debug("Completing existing task: %s" % st_task.name)
        self._sync_task(st_task, ticket, old_values, author)

    def _do_ticket_updated(self, ticket, old_values, author):
        """
        Some change has been made to the ticket. Update the task if necessary.
        """

        #
        # First check if anything of note has actually changed. This is coupled
        # somewhat with _update_task.
        #
        for key in ('summary', 'milestone', 'keywords', 'cc', 'slimtimer_id'):
            if key in old_values.keys():
                break
        else:
            #
            # Nothing of relevance changed. Skip update.
            #
            self.log.debug("Nothing of relevance changed. Skipping update.")
            return

        st_task = self._get_task(ticket, create = True,
                                 old_values = old_values)
        if not st_task:
            return

        self.log.debug("Updating task: %s" % st_task.name)
        self._sync_task(st_task, ticket, old_values, author)

    def _do_ticket_deleted(self, ticket):
        """
        The ticket has been deleted. Complete the task.
        """

        st_task = self._get_task(ticket, create = False)
                                 
        if not st_task:
            return

        st_task.complete = True

        self.log.debug("Completing deleted task: %s" % st_task.name)
        try:
            st_task.update()
        except Exception,e:
            self.log.error("Could not update task: %s (%s)" % 
                           (st_task.name, e))

    def _get_session(self, ticket):
        """
        Get the SlimTimer session
        """

        #
        # Get the task name for using in error messages
        #
        task_name = self._get_st_task_name(ticket)

        # 
        # Get the trac username
        #
        trac_user = ticket.values.get('owner','')
        if not trac_user:
            self.log.warn(
                    "Tried to update ticket (\"%s\") but it has no owner." %
                    task_name)
            return None

        #
        # Get the trac to ST user mapping
        #
        users = self._get_user_mapping()
        if not users:
            self.log.error(
                    "Couldn't get users listing for updating ticket: %s" %
                    task_name)
            return None

        st_user = users.get_st_user(trac_user)
        if not st_user:
            self.log.warn("This ticket (\"%s\") is owned by a user (\"%s\")"\
                          " who is not listed as a SlimTimer user." %
                          (task_name, trac_user))
            return None

        username = st_user.get('st_user','')
        password = st_user.get('st_pass','')
        api_key  = self.config.get('slimtimer', 'api_key')

        if not username or not api_key:
            self.log.warn("Missing username or API key for SlimTimer login."\
                " Task (\"%s\") will not be updated" % task_name)
            return None

        try:
            st = ST.SlimTimerSession(username, password, api_key)
        except:
            self.log.error("Could not log in to SlimTimer with username %s,"\
                           " password %s character(s) in length, and API "\
                           "key %s." % (username, len(password), api_key))
            return None

        return st

    def _get_user_mapping(self):
        """
        Get the object that maps trac users to ST users
        """
        config_file = self._get_user_config_file()
        return Users(config_file)

    def _get_user_config_file(self):
        """
        Get the filename of the user configuration file
        """
        return os.path.join(self.env.path, 'conf', 'users.xml')

    def _get_task(self, ticket, create = False, old_values = {}):
        """
        Get the ST task using the ticket's ST ID or name.
        """

        st_task = None

        #
        # Get session
        #
        st = self._get_session(ticket)
        if not st:
            return None

        #
        # Lookup by ID first
        #
        task_id = ticket.values.get('slimtimer_id', 0)
        if task_id:
            st_task = st.get_task_by_id(task_id)

        if st_task:
            return st_task

        #
        # Lookup by name next
        #
        task_name = self._get_st_task_name(ticket, old_values)
        st_task = st.get_task_by_name(task_name)

        if st_task:
            return st_task

        #
        # Nope, we have to make a new task
        #
        if create:
            st_task = ST.SlimTimerTask(st, task_name)
            self.log.debug("Creating new task: %s" % task_name)

        return st_task

    def _get_st_task_name(self, ticket, old_values = {}):
        """
        Gets the task name for a ticket. If old_values is provided and has
        a value for summary, it will be used instead.
        """
        if (old_values.get('summary')):
            summary = old_values['summary']
        else:
            summary = ticket.values.get('summary', '(No summary)')

        return "#%s: %s" % (ticket.id, summary)

    def _sync_task(self, st_task, ticket, old_values, author):
        """
        Update the SlimTimer task and the trac ticket.
        """
        self._update_task(st_task, ticket, old_values)
        self._update_ticket(ticket, st_task, author)

    def _update_task(self, st_task, ticket, old_values):
        """
        Update the SlimTiemr task with information from the trac ticket.
        """

        #
        # Update name
        #
        # Sometimes the old name will be set and we need to update it (so
        # definitely DON'T pass in old_values here)
        #
        st_task.name = self._get_st_task_name(ticket)

        #
        # Tags
        #
        # We want to preserve the tags already defined on this task and only
        # add and remove the tags that have changed in trac. This way the user
        # can add their own tags in SlimTimer and updating via trac won't
        # interfere with them.
        #
        new_milestone = ticket.values.get('milestone', '')
        new_keywords  = ticket.values.get('keywords', '')
        new_tags = ','.join(filter(lambda x: x, (new_milestone, new_keywords)))

        old_milestone = old_values.get('milestone', '')
        old_keywords  = old_values.get('keywords', '')
        old_tags = ','.join(filter(lambda x: x, (old_milestone, old_keywords)))

        added, removed = self._diff_tags(old_tags, new_tags)
        st_task.tags = self._apply_diff(st_task.tags, added, removed)

        #
        # Coworkers and reporters
        #
        if st_task.id < 1:
            st_task.coworkers = self._get_updated_coworkers_list(ticket,
                                                old_values, st_task.coworkers)

        try:
            st_task.update()
        except Exception,e:
            self.log.error("Could not update task: %s (%s)" % (task_name, e))

    def _parse_tags(self, tags_text):
        """
        Split a comma separated list of tags
        """
        pat = r'"[^"]*"|[^," \t][^,"]+[^," \t]'
        return re.findall(pat, tags_text)

    def _diff_tags(self, old_tags, new_tags):
        """
        Compare (case-insensitive) two lists of tags and find the differences
        """

        #
        # Sorry about this mess. I don't know Python at all. I want to preserve
        # the case of the input in the output whilst also doing a case
        # insensitive comparison.
        #
        old_list = self._parse_tags(old_tags)
        new_list = self._parse_tags(new_tags)

        old_lower = map((lambda x: lower(x)), old_list)
        new_lower = map((lambda x: lower(x)), new_list)

        added   = filter((lambda x: lower(x) not in old_lower), new_list)
        removed = filter((lambda x: lower(x) not in new_lower), old_list)

        return added, removed

    def _apply_diff(self, target, add, remove):
        """
        Apply additions and removals to a list
        """

        #
        # As with _diff_tags we want to preserve the case of the input in the
        # output whilst also doing a case insensitive comparison. There are
        # surely many better ways to do this.
        #
        remove_lower = map((lambda x: lower(x)), remove)
        target_lower = map((lambda x: lower(x)), target)

        return filter((lambda x: lower(x) not in remove_lower), target) + \
               filter((lambda x: lower(x) not in target_lower), add)

    def _get_updated_coworkers_list(self, ticket, old_values, current_list):
        """
        Do some magic to create a list of coworkers
        """

        #
        # XXX All of this is probably unnecessary as we now only update
        # coworkers when we create the ticket
        #

        #
        # As with the tags, do a diff between the current CC and the past one
        #
        new_cc = ticket.values.get('cc', '')
        old_cc = old_values.get('cc', '')
        added, removed = self._diff_tags(old_cc, new_cc)
        result = self._apply_diff(current_list, added, removed)

        #
        # Also make sure the reporter and default CC list are in there
        #
        result_lower = map((lambda x: lower(x)), result)

        additions = []

        # Add default CCs unless they're the owner
        users = self._get_user_mapping()
        owner = users.get_st_user(ticket.values.get('owner',''))
        owner_email = ''
        if owner: owner_email = owner.get('st_user','')
        if users:
            additions += \
                filter((lambda x: x != owner_email), users.get_cc_emails())

        result += filter((lambda x: lower(x) not in result_lower), additions)

        return result

    def _update_ticket(self, ticket, st_task, author):
        """
        Update the trac ticket based on the SlimTimer task.
        """

        #
        # Check if anything changed
        #
        id_changed = ticket.values.has_key('slimtimer_id') and \
                     (getint(ticket['slimtimer_id']) < 1 or \
                     getint(ticket['slimtimer_id']) != st_task.id)

        hours_changed = ticket.values.has_key('totalhours') and \
                        getfloat(ticket['totalhours']) != st_task.hours

        if not id_changed and not hours_changed:
            return

        #
        # Get some common information for storing the changes
        #
        db = self.env.get_db_cnx()
        cl = ticket.get_changelog()

        if cl:
            most_recent_change = cl[-1];
            change_time = most_recent_change[0]
        else:
            change_time = ticket.time_created

        raw_ticket = TracTicket(db, ticket.id)

        #
        # Apply ID changes
        #
        if id_changed:
            prev_st_id = ticket.values.get('slimtimer_id')
            new_st_id  = st_task.id
            raw_ticket.set_st_id(prev_st_id, new_st_id, author, change_time)

        #
        # Apply hours changes
        #
        if hours_changed:
            prev_totalhours = ticket.values.get('totalhours')
            new_totalhours  = st_task.hours
            raw_ticket.set_hours(prev_totalhours, new_totalhours, author,
                                 change_time)
            #
            # Update the ticket object too in case another ticket change
            # handler is called after us
            #
            ticket['totalhours'] = str(st_task.hours)
            ticket['hours'] = '0'

