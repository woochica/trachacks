#!/usr/bin/python
import sys
import re

import trac.env

def main():
    """Update the tickets that were set to Pending status via the custom ticket
       attrib to the new 'pending' status supported by the trac workflow
    """
    if len(sys.argv) != 2:
        print "Usage: %s path_to_trac_environment" % sys.argv[0]
        sys.exit(1)
    tracdir = sys.argv[1]
    trac_env = trac.env.open_environment(tracdir)

    # Update the config...
    custom_vals = trac_env.config.options('ticket-custom')
    for name, value in custom_vals:
        if re.match(r'^pending(?:\.(.*)|$)', name):
            trac_env.config.remove('ticket-custom', name)
    trac_env.config.save()

    # Update the ticket statuses...
    db = trac_env.get_db_cnx()
    cursor = db.cursor()
    cursor.execute("UPDATE ticket SET status = 'pending' "
                   "FROM ticket_custom "
		   "WHERE ticket.status <> 'closed' "
                   "AND ticket_custom.ticket = ticket.id "
		   "AND ticket_custom.name = 'pending' "
		   "AND ticket_custom.value = '1' ")
    #I don't think these hurt anything
    #cursor.execute("DELETE FROM ticket_custom WHERE name=%s", ('pending',))
    db.commit()

if __name__ == '__main__':
    main()

