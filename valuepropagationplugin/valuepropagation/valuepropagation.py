# Copyright 2010 SIXNET, LLC.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301
# USA

"""
ValuePropagation Plugin
author: Chris Nelson <Chris.Nelson@SIXNET.com>
version: 0.1

Update values in other tickets based on ticket changes.  For example,
with Subtickets plugin and Timing and Estimation plugin in place, a
parent ticket's estimate may be the sum of its children's estimates.
This plugin can update the parent when any children change.

There are three types of relationships:

 * self - the "other" ticket is the current ticket (update another field)

 * link - the other tickets are listed in a field of this ticket

 * query - the other tickets can be queried based on this ticket's ID

There are several methods of updating the other ticket's value:

 * sum - add this ticket's value to the other ticket's value.  (This
   ticket's old value is subtracted first.)  Essentially:
     oldOther[to] -= old_values[from]
     newOther[to] += ticket[from]

 * min - the other ticket's value is the minimum of it's old value and
   this ticket's value

 * max - the other ticket's value is the maximum of it's old value and
   this ticket's value

 * suffix - this ticket's value is added as a suffix to the other
   ticket's value.  (This ticket's old value is removed first.)

 * prefix - this ticket's value is added as a prefix to the other
   ticket's value. (This ticket's old value is removed first.)

Other desirable methods which are not yet implemented:

 * union: like sum but field f is a list (set)

 * set:  other's f2 is ticket's f1.

FIXME - A system of pluggable types and methods would be nice.


When the enum priority changes, the pseudo-field "priority_value" is
available for processing.


Configuration looks something like:

[value_propagation]
r1.type = link
r1.link = parents
r1.fields = estimatedhours, hours
r1.method.estimatedhours = sum
r1.method.hours = sum

r2.type = query
r2.query = SELECT child FROM subtickets WHERE parent = %s
r2.fields = effpriority
r2.method.effpriority = prefix

r3.type = self
r3.fields = priority:effpriority
r2.method.priority = suffix

"""

import re
import datetime
import dateutil.tz

from genshi.builder import tag

from trac.core import *
from trac.resource import ResourceNotFound
from trac.ticket import ITicketChangeListener, Ticket
from trac.ticket.web_ui import TicketModule
from trac.util import get_reporter_id


class ValuePropagationPlugin(Component):
    implements(ITicketChangeListener)

    def __init__(self):
        # Cache enum lookups (just priority for now)
        # FIXME - get all enums?
        self.p_values = {}
        self.enums = {}
        self.enums['priority_value'] = 'priority'

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT name," + 
                       db.cast('value', 'int') + 
                       " FROM enum WHERE type=%s", ('priority',))
        for name, value in cursor:
            self.p_values[name] = value

        # ============================================================
        # A propagation method is called from a ticket change listener
        # and takes the following arguments:
        #   ticket - The ticket that changed
        #   old_values - The old values for changed fields of the ticket
        #   from - The changed field to process
        #   to - The field to update based on from
        #   oldOther - The old linked ticket
        #   newOther - The new linked ticket (maybe == oldOther)
        #   options - The configuration options for the relationship
        #
        # The method must update one of the *Other tickets because
        # those are the ones saved by the calling function.


        # Other's value is the sum of my value.
        def _method_sum(ticket, old_values, f, t, oldOther, newOther, options):
            # When creating a ticket, there's no old value to subtract.
            if f in old_values and old_values[f]:
                oldOther[t] = str(float(oldOther[t]) - float(old_values[f]))
            newOther[t] = str(float(newOther[t]) + float(ticket[f]))

        # Other's value is the min of my value and other's old value
        def _method_min(ticket, old_values, f, t, oldOther, newOther, options):
            otherV = float(newOther[t])
            myV = float(ticket[f])
            if (myV < otherV):
                newOther[t] = str(myV)

        # Other's value is the max of my value and other's old value
        def _method_max(ticket, old_values, f, t, oldOther, newOther, options):
            otherV = float(newOther[t])
            myV = float(ticket[f])
            if (myV > otherV):
                newOther[t] = str(myV)

        # See if there's a default for missing values
        def _get_default(ticket, options):
            self.env.log.debug("Getting default for %s" % ticket.id)
            dft = ''
            for n, v in options:
                self.env.log.debug("Processing (%s,%s)" % (n,v))
                # Default option is "<relation>.default"
                p=n.split('.')
                if p[1]=='default':
                    self.env.log.debug("Found default")
                    p=v.split(':')
                    link = p[0]
                    field = p[1]
                    self.env.log.debug("link:%s, field:%s" % (link,field))
                    if link == 'id':
                        other=Ticket(self.env, ticket.id)
                    else:
                        other=Ticket(self.env, ticket[link])
                    self.env.log.debug("other is %s" % other.id)
                    dft = other[field]
                    self.env.log.debug("dft set to %s" % dft)
            return dft
                
        # When my value changes, replace my old value at the end of
        # other's value.
        def _method_suffix(ticket, old_values, f, t, oldOther, newOther, options):
            v = oldOther[t]
            if v == None or v == '':
                v = _get_default(ticket, options)
                v=v.split(',')
            else:
                v=v.split(',')
                v.pop()
            v.append(str(ticket[f]))
            v = ','.join(v)
            newOther[t] = v

        # When my value changes, replace my old value at the beginning
        # of the other's value
        def _method_prefix(ticket, old_values, f, t, oldOther, newOther, options):
            # First remove my old value from the beginning of the oldOther's
            # When creating a ticket, there's no old value to remove.
            if f in old_values and old_values[f]:
                otherV = oldOther[t].split(',')
                myOldV = old_values[f].split(',')
                otherV = otherV[len(myOldV):]
                oldOther[t]=','.join(otherV)

            # Next, add my value to the beginning of newOther's
            otherV = newOther[t].split(',')
            myV = ticket[f].split(',')
            otherV= myV + otherV
            newOther[t] = ','.join(otherV)


        self.methods={}
        self.methods['sum'] = _method_sum
        self.methods['min'] = _method_min
        self.methods['max'] = _method_max
        self.methods['suffix'] = _method_suffix
        self.methods['prefix'] = _method_prefix

        # ============================================================
        # Currently "link", "query", and "self". "link" might be
        # called "internal" (based on ticket or ticket_custom field)
        # and "query" called "external" (based on an external relation
        # such as mastertickets or subtickets).
        self.types={}
        self.types['link']=self._handle_link
        self.types['query']=self._handle_query
        self.types['self']=self._handle_self

        # FIXME - it'd be nice to iterate over configuration here and
        # log unknown types and methods.  Then take that out of
        # _propagate().

    # FIXME - methods functions are private to __init__ (above).  Type
    # functions are "static" (_ prefix) but internal to __init__.  Is
    # there a benefit to one over the other.  I'm just playing here.

    # Update another field on the current ticket
    def _handle_self(self, r, ticket, old_values):
        self._propagate(r, ticket, old_values, ticket.id, ticket.id)

    # Update another ticket based on an ID stored in a field of this
    # ticket
    #
    # NOTE: This is the only type for which oldOther and newOther are
    # different.
    def _handle_link(self, r, ticket, old_values):
        # Get the field used for the link.  ticket[f] has the ID of
        # the dependent ticket.
        # FIXME - iterate over f as a list for blockedby, etc.
        f = self.config.get('value_propagation','%s.link' % r, default=None)
        if f == None:
            self.env.log.debug("%s has no link field configured" % r)
        else:
            if ticket[f]:
                newOtherID=ticket[f]
                # If the linking field changed, get the old other ticket
                if f in old_values:
                    oldOtherID=old_values[f]
                # Otherwise, the old other is the same as the new
                else:
                    oldOtherID=newOtherID
                self._propagate(r, ticket, old_values, oldOtherID, newOtherID)
            else:
                self.env.log.debug("%s is empty" % f)

    # Update other tickets based on a query which returns their IDs,
    # for example from the mastertickets or subtickets tables.
    def _handle_query(self, r, ticket, old_values):
        # Get the query string
        q = self.config.get('value_propagation','%s.query' % r, default=None)
        if q == None:
            self.env.log.debug("%s has no query configured" % r)
        else:
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute(q, (ticket.id,))
            for id in [int(row[0]) for row in cursor]:
                self._propagate(r, ticket, old_values, id, id)


    # Propagate values from ticket to the ticket whose ID is
    # newOtherID.  For link type propagations, oldOtherID may be
    # different than newOtherID if the link field changes value.
    def _propagate(self, relation, ticket, old_values, oldOtherID, newOtherID):
        newOther=Ticket(self.env, newOtherID)
        if newOtherID == oldOtherID or otherID == '':
            oldOther=newOther
        else:
            oldOther=Ticket(self.env, oldOtherID)

        # Only save is a propagation method gets invoked below.
        changed = False

        # Process the fields related to this relationship
        fields = self.config.getlist('value_propagation','%s.fields' % relation)
        for p in fields:
            # Each element is in the form from[:to]
            l = p.split(':')
            if len(l) == 1:
                l.append(p)
            (f, t) = l

            # See if something we care about changed
            if len(old_values) == 0 or \
                    (f in old_values) or \
                    (f in self.enums and self.enums[f] in old_values):
                changed = True

                # If f is an enum (e.g., priority_value) get that value by
                # looking up the display name
                if f in self.enums:
                    ticket[f] = self.p_values[ticket[self.enums[f]]]
                    if self.enums[f] in old_values:
                        old_values[f] = self.p_values[old_values[self.enums[f]]]

                # Call the method for the propagated field
                method=self.config.get('value_propagation','%s.method.%s' % 
                                       (relation, f))
                if method in self.methods:
                    options = self.config.options('value_propagation')
                    options = [(n,v) for n,v in options if n.startswith(relation+'.')]
                    self.methods[method](ticket, old_values, f, t,
                                         oldOther, newOther, options)
                else:
                    self.env.log.debug("No %s method found" % method)

                if f in self.enums:
                    ticket[f] = None
                    if f in old_values:
                        old_values[f] = None

        if changed:
            def _update_ticket(ticket):
                # Determine sequence number.
                cnum = 0
                tm = TicketModule(self.env)
                db = self.env.get_db_cnx()
                for change in tm.grouped_changelog_entries(ticket, db):
                    # FIXME - should this say "and change['cnum'] > cnum?
                    if change['permanent']:
                        cnum = change['cnum']
                # FIXME - Put something in the message?
                # FIXME - the ticket_changed method gets an author, should
                # this say "value propagation on behalf of <author>"?
                ticket.save_changes('value propagation', '', when, db, cnum+1)

            # All the propagation is done, save the new values
            when = datetime.datetime.now()
            tzlocal = dateutil.tz.tzlocal()
            when = when.replace(tzinfo = tzlocal)

            _update_ticket(newOther)
            if newOther != oldOther:
                _update_ticket(oldOther)


    # ITicketChangeListener methods

    def ticket_created(self, ticket):
        self.ticket_changed(ticket, ticket.values.get('description'),
                            ticket.values.get('reporter'), [])


    def ticket_changed(self, ticket, comment, author, old_values):
        # Find the configured propagations (anything in
        # [value_propagation] that has a name like "*.type").

        options=self.config.options('value_propagation')
        for n, v in options:
            p = n.split(".")
            if len(p) == 2 and p[1] == 'type':
                if v in self.types:
                    self.types[v](p[0], ticket, old_values)
                else:
                    self.env.log.debug("%s has an unknown type '%s'" % (n, v))

        
    def ticket_deleted(self, ticket):
        self.env.log.debug("valuePropagation noted ticket %d deleted", ticket.id)
