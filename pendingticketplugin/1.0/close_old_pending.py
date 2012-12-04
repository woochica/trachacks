#!/usr/bin/env python

# Script to close old tickets that are in Pending status.
# Copyright 2007 Daniel A. Atallah <datallah@pidgin.im>
#
# It should be called via cron on a daily basis to close old tickets:

# TRAC_ENV=/somewhere/trac/project/
# DAYS_PENDING=14

# /usr/bin/python /path/to/trac_scripts/close_old_pending.py \
#  -p "$TRAC_ENV" -d $DAYS_PENDING

AUTHOR='trac-robot'
MESSAGE="This ticket was closed automatically by the system.  " \
        "It was previously set to a Pending status and hasn't been updated within %s days."

import sys
import time
from datetime import datetime, timedelta
from optparse import OptionParser

from trac.env import open_environment
from trac.ticket.notification import TicketNotifyEmail
from trac.ticket import Ticket
from trac.ticket.web_ui import TicketModule
from trac.web.href import Href
from trac.util.datefmt import utc, to_utimestamp


parser = OptionParser()
parser.add_option('-p', '--project', dest='project',
                  help='Path to the Trac project.')
parser.add_option('-d', '--daysback', type='int', dest='maxage', default=14,
                  help='Timeout for Pending Tickets to be closed after.')

(options, args) = parser.parse_args(sys.argv[1:])

class CloseOldPendingTickets:

    def __init__(self, project=options.project, author=AUTHOR,
                     maxage=options.maxage):

        try:
            self.env = open_environment(project)
            db = self.env.get_db_cnx()
            cursor = db.cursor()

            msg = MESSAGE % (maxage)

            now = datetime.now(utc)
            maxtime = to_utimestamp(now - timedelta(days=maxage))

            cursor.execute("SELECT id FROM ticket " \
                           "WHERE status = %s " \
                           "AND changetime < %s ", ('pending', maxtime))
    
            rows = cursor.fetchall()

            for row in rows:
                id = row[0]
                try:
                    ticket = Ticket(self.env, id, db);

                    ticket['status'] = 'closed'

                    # determine sequence number...
                    cnum = 0
                    tm = TicketModule(self.env)
                    for change in tm.grouped_changelog_entries(ticket, db):
                        c_cnum = change.get('cnum', None)
                        if c_cnum and int(c_cnum) > cnum:
                            cnum = int(c_cnum)

                    ticket.save_changes(author, msg, now, db, str(cnum + 1))
                    db.commit()

                    print 'Closing Ticket %s (%s)' % (id, ticket['summary'])

                    tn = TicketNotifyEmail(self.env)
                    tn.notify(ticket, newticket=0, modtime=now)
                except Exception, e:
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                    print>>sys.stderr, 'Unexpected error while processing ticket ' \
                                   'ID %s: %s' % (id, e)
        except Exception, e:
               import traceback
               traceback.print_exc(file=sys.stderr)
               print>>sys.stderr, 'Unexpected error while retrieving tickets '


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "For usage: %s --help" % (sys.argv[0])
    else:
        CloseOldPendingTickets()
