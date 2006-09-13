# Copyright (C) 2006 Sam Bloomquist <spooninator@hotmail.com>
# All rights reserved.
#
# This software may at some point consist of voluntary contributions made by
# many individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Author: Sam Bloomquist <spooninator@hotmail.com>

import time
import sys

from trac.core import *
from trac.util import format_date
from trac.env import open_environment

def main():
    if len(sys.argv) != 2:
        print >> sys.stderr, 'Must supply a trac_env as an argument to the burndown_job'
        sys.exit(1)
        
    env_path = sys.argv[1]
    
    # today's date
    today = format_date(int(time.time()))
    
    # open up a connection to the trac database
    env = open_environment(env_path)
    db = env.get_db_cnx()
    cursor = db.cursor()
    
    # make sure that there isn't already an entry for today in the burndown table
    cursor.execute("SELECT id FROM burndown WHERE date = '%s'" % today)
    row = cursor.fetchone()
    needs_update = False
    if row:
        print >> sys.stderr, 'burndown_job.py has already been run today - update needed'
        needs_update = True
    else:
        print >> sys.stderr, 'first run of burndown_job.py today - insert needed'
    
    # get arrays of the various components and milestones in the trac environment
    cursor.execute("SELECT name AS comp FROM component")
    components = cursor.fetchall()
    cursor.execute("SELECT name, started, completed FROM milestone")
    milestones = cursor.fetchall()
    
    for mile in milestones:
        if mile[1] and not mile[2]: # milestone started, but not completed
            for comp in components:
                sqlSelect =     "SELECT est.value AS estimate, ts.value AS spent "\
                                    "FROM ticket t "\
                                    "    LEFT OUTER JOIN ticket_custom est ON (t.id = est.ticket AND est.name = 'estimatedhours') "\
                                    "    LEFT OUTER JOIN ticket_custom ts ON (t.id = ts.ticket AND ts.name = 'totalhours') "\
                                    "WHERE t.component = '%s' AND t.milestone = '%s' "
                cursor.execute(sqlSelect % (comp[0], mile[0]))
            
                rows = cursor.fetchall()
                hours = 0
                estimate = 0
                spent = 0
                if rows:
                    for estimate, spent in rows:
                        if not estimate:
                            estimate = 0
                        if not spent:
                            spent = 0
                    
                        hours += float(estimate) - float(spent)
                
                if needs_update:
                    cursor.execute("UPDATE burndown SET hours_remaining = '%f' WHERE date = '%s' AND milestone_name = '%s'"\
                                        "AND component_name = '%s'" % (hours, today, mile[0], comp[0]))
                else:
                    cursor.execute("INSERT INTO burndown(id,component_name, milestone_name, date, hours_remaining) "\
                                        "    VALUES(NULL,'%s','%s','%s',%f)" % (comp[0], mile[0], today, hours))
                                     
    db.commit()

if __name__ == '__main__':
    main()
