# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import time

from trac import core
from trac.ticket import api, model

class TracDupPlugin(core.Component):
    core.implements(api.ITicketChangeListener)
    core.implements(api.ITicketManipulator)

    # helper methods
    def _add_master(self, author, dup_id, master_id):
        """
        Update the master ticket(s) to reflect the duplication.

        Updates custom dup fields of master and recurses up.
        Also adds comments.

        @type  dup_id:    object with __str__
        @type  master_id: object with __str__
        """
        self.env.log.debug("master: dupping %s to %s" % (dup_id, master_id))

        # tag the master ticket at each step
        cmt = u"Ticket #%s has been closed as a " \
            "duplicate of ticket #%s." % (dup_id, master_id)

        self._update_master(author, cmt, master_id)

    def _remove_master(self, author, dup_id, master_id):
        """
        Update the master ticket(s) to reflect removal of duplication.

        Updates custom dup fields of master and recurses up.
        Also adds comments.

        @type  dup_id:    object with __str__
        @type  master_id: object with __str__
        """
        self.env.log.debug("master: undupping %s to %s" % (dup_id, master_id))

        # tag the master ticket at each step
        cmt = u"Ticket #%s has been removed as a " \
            "duplicate of ticket #%s." % (dup_id, master_id)

        self._update_master(author, cmt, master_id)

    def _update_master(self, author, cmt, master_id):
        """
        @type  master_id: object with __str__
        """
        # helper method for dupping and undupping
        while master_id:
            master = model.Ticket(self.env, master_id)

            if self._recalculate_ticket(master):
                self.env.log.debug(
                    "adding comment to master ticket %s" % master_id)
                # FIXME:
                # this can raise OperationalError if the column does not exist
                # can we throw a nicer error ?
                # for example, check the configuration to see that custom
                # fields are there ?
                master.save_changes(author, cmt)

            # recurse up
            master_id = master.values.get('dup_of', None)

    def _recalculate_ticket(self, ticket):
        """
        Recalculate dups and dup_count fields of the given ticket.

        @returns: whether the ticket was changed and needs committing
        """
        ids = self._get_dups_recursively(ticket.id)

        dups = ", ".join([str(i) for i in ids])
        dup_count = len(ids)

        if ticket.values.get('dups', None) == dups \
         and int(ticket.values.get('dup_count', '')) == dup_count:
            return False

        self.env.log.debug('Recalculated ticket %s with dups %s (%d)' % (
            ticket.id, dups, dup_count))

        ticket['dups'] = dups
        ticket['dup_count'] = str(dup_count)

        # delete fields if there are no dups
        if dup_count == 0:
            ticket['dups'] = None
            ticket['dup_count'] = None

        return True

    def _get_dups(self, ticket_id):
        """
        Get all the direct dups of a given ticket.

        @type ticket_id: int

        @returns: list of int
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
SELECT t.id, c.value
FROM ticket t, ticket_custom c
WHERE c.name='dup_of' AND t.id=c.ticket AND c.value=%s
""" % ticket_id)
        ids = []
        for dup_id, m_id in cursor:
            ids.append(dup_id)

        return ids

    def _get_dups_recursively(self, ticket_id):
        """
        Get all the dups of a given ticket, and recurse into their
        dups.

        @type ticket_id: object with __str__

        @returns: list of int
        """
        res = []

        ids = self._get_dups(ticket_id)
        for i in ids:
            res.append(i)
            res.extend(self._get_dups_recursively(i))

        return res

    def _add_dup(self, author, dup, master_id):
        """
        Update the dup ticket to reflect the duplication.

        @type  dup:       L{trac.ticket.model.Ticket}
        @type  master_id: object with __str__
        """
        self.env.log.debug("dup: dupping %s to %s" % (dup.id, master_id))
        self._add_master(author, dup.id, master_id)

        # tag this ticket and close it
        cmt = u"Duplicate of ticket #%s." % master_id
        self.env.log.debug(
            "adding comment to dup ticket %s" % dup.id)
        # FIXME: ugly hack to avoid
        # IntegrityError: columns ticket, time, field are not unique
        time.sleep(1)
        dup['status'] = u'closed'
        dup['resolution'] = u'duplicate'

        dup.save_changes(author, cmt)

    def _remove_dup(self, author, dup, master_id):
        """
        Update the dup ticket to reflect the unduplication.
        """
        self.env.log.debug("dup: undupping %s to %s" % (dup.id, master_id))
        self._remove_master(author, dup.id, master_id)

        # tag this ticket and reopen it
        cmt = u"Not a duplicate of ticket #%s." % master_id
        self.env.log.debug(
            "adding comment to dup ticket %s" % dup.id)
        # FIXME: ugly hack to avoid
        # IntegrityError: columns ticket, time, field are not unique
        import time; time.sleep(1)
        dup['status'] = u'reopened'

        dup.save_changes(author, cmt)

 
    # ITicketChangeListener implementation
    def ticket_created(self, ticket):
        """Called when a ticket is created."""

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified.

        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """
        self.env.log.debug("ticket_changed: %s" % ticket.id)

        if old_values.get('status', None) == 'closed' \
            and ticket.values.get('dup_of', None):
            self.env.log.debug("ticket_changed: "
                'duplicate ticket %s reopened, removing dup_of' % ticket.id)
            # unsetting it will trigger this method again anyway
            time.sleep(1)
            ticket['dup_of'] = None
            ticket.save_changes(author, "Removing dup_of value.")
            return

        # ignore if dup_of was not changed, or set to None (the first time)
        if not old_values.has_key('dup_of'):
            self.env.log.debug(
                "No dup_of change on %s" % ticket.id)
            return

        # ignore if dup_of did not really get a new value
        master_id = ticket.values['dup_of']

        # also possible to go from None to '', when updating a ticket
        # created before dup_of was a custom key
        if old_values.get('dup_of', None) == None and master_id == '':
            self.env.log.debug(
                'dup_of was added to %s without a value, return' % ticket.id)
            return

        if master_id == old_values.get('dup_of', None):
            self.env.log.debug(
                "No dup_of change on %s" % ticket.id)
            return

        if not master_id:
            master_id = old_values['dup_of']
            # dup_of was removed, so break the chain
            self._remove_dup(author, ticket, master_id)
        else:
            # dup_of was added/updated
            self._add_dup(author, ticket, master_id)

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""

    # ITicketManipulator implementation
    def prepare_ticket(self, req, ticket, fields, actions):
        """Not currently called, but should be provided for future
        compatibility."""
       
    def validate_ticket(self, req, ticket):
        """Validate a ticket after it's been populated from user input.
       
        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with the
        ticket. Therefore, a return value of `[]` means everything is OK."""

        res = []

        # the ticket we receive is a temporary not-yet-commited ticket
        # and contains fields set that weren't changed as well,
        # retrieve the original one so we can compare
        ot = model.Ticket(self.env, ticket.id)

        self.env.log.debug('validate_ticket: %s' % ticket.id)

        # refuse changes to dup_count and dups fields
        new = ticket.values.get('dups', None)
        if new is not None and new != ot.values.get('dups', None):
            res.append(('dups', 'Cannot manually change the dups field.'))
            return res

        new = ticket.values.get('dup_count', None)
        if new is not None and new != ot.values.get('dup_count', None):
            res.append(('dup_count',
                'Cannot manually change the dup_count field.'))
            return res

        new_id = ticket.values.get('dup_of', None)

        # allow unsetting
        if not new_id:
            self.env.log.debug("validate_ticket: dup_of is None, so fine")
            return res

        # care only about tickets that have dup_of changes
        old = ot.values.get('dup_of', None)
        if old == new_id:
            self.env.log.debug("validate_ticket: no dup_of changes")
            return res

        # refuse to change closed tickets
        if ticket.values['status'] == u'closed':
            if ticket.values['resolution'] == u'duplicate':
                self.env.log.debug(
                    "validate_ticket: allowing unduplicate to get validated")
                # but still subject to other rules
            else:
                self.env.log.debug(
                    "validate_ticket: refusing to dup closed ticket #%s" %
                        ticket.id)
                res.append(('dup_of',
                    'Ticket is already closed, and not as a duplicate.'))
                return res

        # refuse to dup_of and reopen ticket in one go
        if ot.values['status'] == u'closed' \
            and ticket.values['status'] == u'reopened':
                self.env.log.debug("validate_ticket: "
                    "refusing to dup_of and reopen ticket #%s" %
                        ticket.id)
                res.append(('status',
                    'If you want to duplicate an already closed ticket, '
                    'only change dup_of without reopening the ticket.'))
                return res

        # warn when it starts with #
        if len(new_id) > 0 and new_id[0] == '#':
            res.append(('dup_of',
                'Please enter the ticket number without a leading #.'))
            return res

        # refuse to dup to non-existing tickets; this raises a TracError
        # if it doesn't exist
        # coderanger says a Ticket can have anything with a __str__ method
        # as id
        # except in the 0.10.5dev branch, a non-existing ticket id raises
        # a TracError with %d in the format string (fixed on TRUNK),
        # so make it an int here
        master = model.Ticket(self.env, int(new_id))

        # refuse to dup to self
        if str(new_id) == str(ticket.id):
            self.env.log.debug("validate_ticket: "
                "cowardly refusing to dup to self #%s" % ticket.id)
            res.append(('dup_of',
                'Cannot duplicate a ticket to itself.'))
            return res

        self.env.log.debug('validate_ticket: Validated ticket %s' % ticket.id)
        return res
