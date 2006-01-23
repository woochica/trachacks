from StringIO import StringIO
import re
from time import localtime, strftime, time
import os

def execute(hdf, txt, env):
    out = StringIO()
    db = env.get_db_cnx()

    query = "SELECT name, due, description FROM milestone " \
            "WHERE name != '' " \
            "AND (due IS NULL OR due = 0 OR due > %d) " \
            "ORDER BY (IFNULL(due, 0) = 0) ASC, due ASC, name" % time()

    cursor = db.cursor()
    cursor.execute(query)
    out.write('<ul>\n')
    while True:
        row = cursor.fetchone()
        if not row:
            break
        name = row['name']
        if row['due'] > 0:
            date = strftime('%x', localtime(row['due']))
        else:
            date = "<i>(later)</i>"
        if name == "":
            continue
        out.write('<li> %s - <a href="http://%s%s">%s</a>\n' %
                  (date, os.getenv('HTTP_HOST'),
                   env.href.milestone(name), name))
    out.write('</ul>\n')
    return out.getvalue()
