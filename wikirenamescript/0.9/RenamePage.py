#! /usr/bin/python
from trac.core import *
from trac.env import *
import sys
import sre
import os
import time

if len(sys.argv) < 4:
    print 'Usage: %s old-name new-name [trac-env]' % sys.argv[0]
    sys.exit(1)
else:
    oldname = sys.argv[1]
    newname = sys.argv[2]
    tracenv = sys.argv[3]

env = Environment(tracenv)
db = env.get_db_cnx()
cursor = db.cursor()

sqlbase = ' FROM wiki w1, ' + \
    '(SELECT name, MAX(version) AS VERSION FROM WIKI GROUP BY NAME) w2 ' + \
    'WHERE w1.version = w2.version AND w1.name = w2.name '

sql = 'SELECT w1.version,w1.text' + sqlbase + 'AND w1.name = \'%s\'' % oldname
cursor.execute(sql)

row = cursor.fetchone()

if not row:
    print 'Page not found'
    sys.exit(1)
    
# Funny windows hack
remote_user = ''
if os.name == 'nt':
    remote_user = os.environ['USERNAME']
else:
    remote_user = os.getlogin()

new_wiki_page = (newname,row[0]+1,int(time.time()),remote_user,'127.0.0.1',row[1],'Name changed from %s to %s'%(oldname,newname),0)

# Create a new page with the needed comment
cursor.execute('INSERT INTO wiki (name,version,time,author,ipnr,text,comment,readonly) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)', new_wiki_page)

# Move all the old versions of the page
cursor.execute('UPDATE wiki SET name=%s WHERE name=%s', (newname,oldname))

# Move any attachments that are on the page
cursor.execute('UPDATE attachment SET id=%s WHERE type="wiki" AND id=%s', (newname,oldname))

# Change the directory where the attachments are stored
os.renames(os.path.join(tracenv, 'attachments/wiki', oldname),
    os.path.join(tracenv, 'attachments/wiki', newname))

# Get a list of all wiki pages containing links to the old page
sql = 'SELECT w1.version,w1.name,w1.text' + sqlbase + 'AND w1.text like \'%%[wiki:%s %%\'' % oldname
cursor.execute(sql)

# Rewrite all links to the old page, such as to point to the new page
for row in cursor:
    newtext = sre.sub('\[wiki:%s '%oldname,'[wiki:%s '%newname,row[2])
    cursor.execute('UPDATE wiki SET text=%s WHERE name=%s AND version=%s', (newtext,row[1],row[0]))

db.commit()

