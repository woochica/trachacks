#! /usr/bin/python
import sqlite
import sys
import sre
import os
import time

if len(sys.argv) < 3:
    print 'Usage: %s old-name new-name [trac-env]' % sys.argv[0]
    sys.exit(1)
else:
    oldname = sys.argv[1]
    newname = sys.argv[2]

if len(sys.argv) > 3:
    trackenv = sys.argv[3]
else:
    tracenv = '/var/trac/helpdesk'


db = sqlite.connect(tracenv+'/db/trac.db', mode=0555)
q = db.cursor()

sqlbase = ' FROM wiki w1, ' + \
    '(SELECT name, MAX(version) AS VERSION FROM WIKI GROUP BY NAME) w2 ' + \
    'WHERE w1.version = w2.version AND w1.name = w2.name '

sql = 'SELECT w1.version,w1.text' + sqlbase + 'AND w1.name = \'%s\'' % oldname
q.execute(sql)

row = q.fetchone()

if not row:
    print 'Page not found'
    sys.exit(1)

new_wiki_page = (newname,row[0]+1,int(time.time()),os.getlogin(),'127.0.0.1',row[1],'Name changed from !%s to !%s'%(oldname,newname),0)

# Create a new page with the needed comment
sql = 'INSERT INTO wiki (name,version,time,author,ipnr,text,comment,readonly) VALUES ("%s",%s,%s,"%s","%s","%s","%s",%s)' % new_wiki_page
q.execute(sql)

# Move all the old versions of the page
sql = 'UPDATE wiki SET name="%s" WHERE name="%s"' % (newname,oldname)
q.execute(sql)

# Move any attachments that are on the page
sql = 'UPDATE attachment SET id="%s" WHERE type="wiki" AND id="%s"' % (newname,oldname)
q.execute(sql)

# Get a list of all wiki pages containing links to the old page
sql = 'SELECT w1.version,w1.name,w1.text' + sqlbase + 'AND w1.text like \'%%[wiki:%s %%\'' % oldname
q.execute(sql)

# Rewrite all links to the old page, such as to point to the new page
for row in q:
    newtext = sre.sub('\[wiki:%s '%oldname,'[wiki:%s '%newname,row[2])
    sql = 'UPDATE wiki SET text="%s" WHERE name="%s" AND version=%s'%(newtext,row[1],row[0])
    q.execute(sql)

db.commit()

