"""Fit milestones in a Trac milestone table to a new time line.
"""

# reschedule.py $Id$
# Author: Terry Brown
# Created: Mon Nov 26 2007

import sys
import time
import datetime
from datetime import date
from optparse import OptionParser

revison = "$Rev$"
url = "$URL$"

def makeParser():
    parser = OptionParser(description="""Fit Trac milestone due dates into a new time range, preserving relative spacing""")
    parser.add_option("-D", "--dbtype", default="sqlite",
                      help="database type: sqlite (default), postgres, mysql")
    parser.add_option("-d", "--dsn",
                      help="connect spec, eg. 'user=foo dbname=bar host=eg.com', or a filename for sqlite systems")
    parser.add_option("-s", "--start",
                      help="new start date YYYYMMDD")
    parser.add_option("-e", "--end",
                      help="new end date YYYYMMDD")
    parser.add_option("-o", "--old",
                      help="old start date YYYYMMDD")
    parser.add_option("-S", "--schema", default='',
                      help="name of schema containing milestone table")
    parser.add_option("-c", "--commit", default=False, action='store_true',
                      help="commit changes to table")
    parser.add_option("-C", "--comment", default=False, action='store_true',
                      help="include 'Rescheduled from YYYY/MM/DD to YYYY/MM/DD' comments")
    parser.add_option("-v", "--verbose", default=False, action='store_true',
                      help="show SQL")

    return parser

def main():

    (opt, args) = makeParser().parse_args()

    if opt.dbtype == 'sqlite':
        import sqlite3 as dbmod
    elif opt.dbtype == 'postgres':
        try:
            import psycopg2 as dbmod
        except:
            import psycopg as dbmod
    elif opt.dbtype == 'mysql':
        import MySQLdb as dbmod

    if opt.schema and not opt.schema.endswith('.'): opt.schema += '.'

    connectString = opt.dsn
    if opt.dbtype == 'sqlite':
        conn = dbmod.connect(connectString)
    else:
        conn = dbmod.connect(dsn=connectString)
    curs = conn.cursor()

    fDue, fName, fComp, fNew = range(4)
    # names of fields, fNew to be derived later

    curs.execute('select due, name, completed from %smilestone order by due'
                 % opt.schema)
    res = [list(i) for i in curs.fetchall()]

    fmt = '%Y%m%d'
    ts = lambda x: int(time.mktime(x))
    ds = lambda x: date.fromtimestamp(x).strftime('%b %d %Y')

    # defaults for start, old, and end are fDue in the row indicated
    for o, row in [('start', 0), ('old', 0), ('end', -1)]:
        if not getattr(opt, o):
            setattr(opt, o, res[row][fDue])  # use default
        else:
            setattr(opt, o, ts(time.strptime(getattr(opt, o), fmt)))

    comp = []
    for i in res:
        if i[fComp]:
            comp.append('%s due %s, completed %s' 
                % (i[fName],ds(i[fDue]),ds(i[fComp])))
        else:
            i.append( float(i[fDue]-opt.old) / (res[-1][fDue]-opt.old) *
                      (opt.end - opt.start) + opt.start);
            print '%s -> %s: %s' % (ds(i[fDue]), ds(i[fNew]), i[fName])

            q = ( "update %smilestone set due = %d where name='%s'"
                  % (opt.schema, int(i[fNew]), i[fName]))
            if opt.verbose: print q
            if opt.commit:
                curs.execute(q)
            if opt.comment:
                q = ( "update %smilestone set description = description || "
                      "'\\n\\nRescheduled from %s to %s' where name='%s'"
                      % (opt.schema, ds(i[fDue]), ds(i[fNew]), i[fName]))
                if opt.verbose: print q
                if opt.commit:
                    curs.execute(q)

    if opt.commit:
        conn.commit()

    if comp:
        print ('Completed milestones unchanged:\n%s' 
               % '\n'.join(['  '+i for i in comp]))

if __name__ == '__main__':

    main()
