# Copyright (C) 2008 The Open Planning Project
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
TracBacks Plugin
author: Mel Chua <mchua@openplans.org>
version: 0.1

Detects when a ticket A is referenced in another ticket B and adds
a comment "TracBack: #B" to ticket A.
"""

import re

from genshi.builder import tag

from trac.core import *
from trac.resource import ResourceNotFound
from trac.ticket import ITicketChangeListener, Ticket

class TracBacksPlugin(Component):
    implements(ITicketChangeListener)

    # ITicketChangeListener methods

    def ticket_created(self, ticket):
        # TODO
        # Note that we don't check for tracbacks on ticket
        # creation - it's got to be in a comment. Maybe we
        # can fix this in a later version of the ticket.
        pass

    def ticket_changed(self, ticket, comment, author, old_values):
        pattern = re.compile(r"""
        (?=                    # Don't return '#' character:
           (?<=^\#)            # Look for a TracLink Ticket at the beginning of the string
          |(?<=[\s,.;:!]\#)    # or on a whitespace boundary or some punctuation
        )
        (\d+)                  # Any length ticket number (return the digits)
        (?=
           (?=\b)              # Don't return word boundary at the end
          |$                   # Don't return end of string
        )
        """, re.VERBOSE)
        tickets_referenced = pattern.findall(comment)
        # convert from strings to ints and discard duplicates
        tickets_referenced = set(int(t) for t in tickets_referenced)
        # remove possible self-reference
        tickets_referenced.discard(ticket.id)

        # put trackbacks on the tickets that we found
        trackback_preface = "Trackback: #"
        if trackback_preface not in comment: # prevent infinite recursion
            for ticket_to_trackback in tickets_referenced:
                try:
                    t = Ticket(self.env, ticket_to_trackback)
                except ResourceNotFound: # referenced ticket does not exist
                    continue
                trackback_string = trackback_preface + str(ticket.id)
                t.save_changes(author, trackback_string)

    def ticket_deleted(self, ticket):
        pass
