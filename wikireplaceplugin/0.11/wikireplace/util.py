#! /usr/bin/python
# -*- coding: utf-8 -*-
import sys
import re
import os
import time
import optparse
import urllib

from trac.core import *
from trac.env import *
from trac.util.datefmt import to_datetime, utc

try:
    # Micro-second support added to 0.12dev r9210
    from trac.util.datefmt import to_utimestamp
except ImportError:
    from trac.util.datefmt import to_timestamp
    to_utimestamp = to_timestamp

__all__ = ['main', 'wiki_text_replace']

def pass_(*args): 
    pass
    
def print_(s, *args): 
    print s%args
    
def log_intercept(log):
    def out(s, *args):
        log('WikiReplacePlugin: '+s, *args)
    return out

def wiki_text_replace(env, oldtext, newtext, wikipages, user, ip, debug=False, db=None):
    """Replace oldtext with newtext in all wiki pages in wikipages list using env as the environment.
       wikipages should be a list of wiki pages with optional * and ? wildcards (unix file globbing syntax)
    """
    handle_commit = False
    if not db:
        db = env.get_db_cnx()
        handle_commit = True
    cursor = db.cursor()
    
    if debug is False:
        debug = pass_
    elif debug is True:
        debug = print_
    else:
        debug = log_intercept(debug)

    sqlbase = ' FROM wiki w1, ' + \
        '(SELECT name, MAX(version) AS max_version FROM wiki GROUP BY name) w2 ' + \
        'WHERE w1.version = w2.max_version AND w1.name = w2.name '

    # Get a list of all wiki pages containing text to be replaced
    debug("Searching all wiki pages containing text")
    
    for wikipage in wikipages:
        sql = 'SELECT w1.version,w1.name,w1.text' + sqlbase + 'AND w1.name glob %s AND w1.text like %s'
        debug('Running query %r', sql)

        cursor.execute(sql, (wikipage, '%'+oldtext+'%'))

        for row in list(cursor):
            debug("Found a page with searched text in it: %s (v%s)", row[1], row[0])
            newcontent = re.sub(oldtext,newtext,row[2])

            # name, version, now, user, ip, newcontent, replace comment
            new_wiki_page = (row[1],row[0]+1,to_utimestamp(to_datetime(None, utc)),user,ip,newcontent,'Replaced "%s" with "%s".'%(oldtext,newtext),0)

            # Create a new page with the needed comment
            debug('Inserting new page %r', new_wiki_page)
            cursor.execute('INSERT INTO wiki (name,version,time,author,ipnr,text,comment,readonly) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)', new_wiki_page)

    if handle_commit:
        db.commit()
