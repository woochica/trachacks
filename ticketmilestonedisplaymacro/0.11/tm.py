"""
Lists all tickets matching a given regular expression

This macro takes one parameter, the regexp
"""

import time
import re
from StringIO import StringIO

revison = "$Rev$"
url = "$URL$"

def execute(hdf, args, env):
    db = env.get_db_cnx()
    cursor = db.cursor()

    sql = "SELECT id, milestone FROM ticket WHERE id = '%s'" % args

    cursor.execute(sql)

    buf = StringIO()

    row = cursor.fetchone()
    if row == None:
      buf.write('Ticket with ID "%s" was not found' % args)
    else:
      buf.write('[<a href="%s">Ticket #%s</a>, <a href="%s">Milestone: %s</a>]' % (env.href.ticket(row[0]), row[0], env.href.milestone(row[1]), row[1]))
    
    return buf.getvalue()