#!/usr/bin/env python

# Script to close old tickets that are in Pending status.
# Copyright 2007 Daniel A. Atallah <datallah@pidgin.im>
#
# It should be called via cron on a daily basis to close old tickets:

# TRAC_ENV=/somewhere/trac/project/
# DAYS_PENDING=14
# TRAC_URL=http://trac.mysite.com/project/

# /usr/bin/python /path/to/trac_scripts/close_old_pending.py \
#  -p "$TRAC_ENV" -d $DAYS_PENDING -s "$TRAC_URL"

#TRAC_ENV='/home/var/trac/pidgin'
AUTHOR='trac-robot'
MESSAGE="This ticket was closed automatically by the system.  " \
        "It was previously set to a Pending status and hasn't been updated within %s days."

#import re
#import os
import sys
import time 

from trac.env import open_environment
from trac.ticket.notification import TicketNotifyEmail
from trac.ticket import Ticket
from trac.web.href import Href

try:
    from optparse import OptionParser
except ImportError:
    try:
         from optik import OptionParser
    except ImportError:
         raise ImportError, 'Requires Python 2.3 or the Optik option parsing library.'

parser = OptionParser()
parser.add_option('-p', '--project', dest='project',
                  help='Path to the Trac project.')
parser.add_option('-d', '--daysback', type='int', dest='maxage', default=14,
                  help='Timeout for Pending Tickets to be closed after.')
parser.add_option('-s', '--siteurl', dest='url',
                  help='The base URL to the project\'s trac website (to which '
                       '/ticket/## is appended).  If this is not specified, '
                       'the project URL from trac.ini will be used.')

(options, args) = parser.parse_args(sys.argv[1:])

class CloseOldPendingTickets:

    def __init__(self, project=options.project, author=AUTHOR,
                     maxage=options.maxage, url=options.url):

        self.env = open_environment(project)
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        if url is None:
		url = self.env.config.get('trac', 'base_url')

	self.env.href = Href(url)
	self.env.abs_href = Href(url)

	self.msg = MESSAGE % (maxage)
	self.now = int(time.time())

	maxtime = int(time.time()) - (60 * 60 * 24 * maxage)
	#maxtime = int(time.time()) - 10

        cursor.execute("SELECT id FROM ticket t, ticket_custom c " \
                       "WHERE t.status <> %s " \
		       "AND t.changetime < %s " \
                       "AND t.id = c.ticket " \
                       "AND c.name = %s " \
                       "AND c.value = %s ", ('closed', maxtime, 'pending', '1'))
    
        rows = cursor.fetchall()

        for row in rows:
	    id = row[0]
	    try:
                ticket = Ticket(self.env, id, db);

                ticket['status'] = 'closed'
		ticket['pending'] = '0';
                #ticket['resolution'] = 'fixed'
        
                ticket.save_changes(author, self.msg, self.now, db, 1)
                db.commit()

                print 'Closing Ticket %s (%s)\n' % (id, ticket['summary'])

                tn = TicketNotifyEmail(self.env)
                tn.notify(ticket, newticket=0, modtime=self.now)
            except Exception, e:
                import traceback
                traceback.print_exc(file=sys.stderr)
                print>>sys.stderr, 'Unexpected error while processing ticket ' \
                                   'ID %s: %s' % (id, e)


if __name__ == "__main__":
	if len(sys.argv) < 3:
		print "For usage: %s --help" % (sys.argv[0])
	else:
		CloseOldPendingTickets()
