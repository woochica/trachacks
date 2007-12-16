"""
        Convert Sycamore postgres data to mysql trac data

        This program was written specifically to convert RocWiki, but
        it may be useful to others who want to migrate from Sycamore to trac.

"""
import sys, os, time, array, re
from trac.util.text import unicode_quote

# we can't use the default dbapi conventions because we're
# using two different databases

my_dbapi = __import__("MySQLdb")
pg_dbapi = __import__("psycopg2")

# set these vars

ATTACHMENTS = '/path/to/trac/instance/attachments/wiki'

mydb = my_dbapi.connect(host='localhost',
                        user='trac',
                        passwd='trac',
                        db='trac')

pgdb = pg_dbapi.connect('''host = \'%s\' user=\'%s\' 
                        password=\'%s\' dbname=\'%s\' ''' 
                        %('localhost',
                          'sycamore',
                          'sycamore',
                          'sycamore'))

# utility functions follow

# get_usernames loads a dictionary with key of id and value of
#               propercased_username 
# conversion notes:
#

def get_usernames(pgc):

    print "Retrieving usernames for user conversion"
    pgc.execute("""SELECT * FROM users """);
    rows = pgc.fetchall()

    count = 0
    users = {}
    for row in rows:
        users[row[0]] = row[22]
        count += 1

    print "Loaded %d users" % count
    return users


# here are the conversion functions.  Most take two parms, 
# pgc = postgres cursor, and myc = mysql cursor.  Some take a third parm,
# users = dictionary of propercased usernames keyed by username

# page_conversions
#       run all the string conversions on the page blob
#

def page_conversions(text_blob):

    # fix 1:  ==text== requiring spaces or it won't work

    r = re.compile(r'(=+)(.*?)(=+)')

    # run an iterator on it.  the iterator returns match objects, and
    # match objects contain the groups of the RE that matched
    for m in r.finditer(text_blob):
        text_blob = text_blob.replace(m.group(1)+m.group(2)+m.group(3),
                                      m.group(1)+' '+m.group(2)+' '+m.group(3))

    # fix 2 - comments.  put the AddComment macro at the end and replace
    # the [[Comments]] marker with a == Comments == heading

    r = re.compile(r'\[\[comments\]\]|\[\[comments\(\s*\)\]\]',re.IGNORECASE)
    for m in r.finditer(text_blob):
        text_blob = text_blob.replace(m.group(0),"\n=== Comments ===")
        text_blob += "\n[[AddComment]]"

    # fix 3 - [[TableofContents]] -> [[PageOutline]]
    r = re.compile(r'\[\[tableofcontents\]\]',re.IGNORECASE)
    for m in r.finditer(text_blob):
        text_blob = text_blob.replace(m.group(0),'[[PageOutline]]')

    # fix 4 - interwiki - wiki:wikipedia -> wikipedia:
    r = re.compile(r'wiki\:wikipedia',re.IGNORECASE)
    for m in r.finditer(text_blob):
        text_blob = text_blob.replace(m.group(0),'wikipedia')

    # fix 5 - ["xxx yyy" desc of xxx yyy] => [wiki:"xxx yyy" desc of xxx yyy ]

    # using 2 re's because non-greedy match didn't seem to work...
    r = re.compile(r'\[(.+?)\]')
    r2 = re.compile(r'(".+?"\s+.+?)')
    for m in r.finditer(text_blob):
        m2 = r2.search(m.group(0))
        if m2:
            text_blob = text_blob.replace(m.group(0),
                                          '[wiki:'+m.group(1)+']')

    # fix 6  * right after newline isn't picked up as bullet

    text_blob = text_blob.replace("\n*","\n *")

    # fix 7 # not recognized as comment - change to Note

    r = re.compile(r'^#(.+)$',re.MULTILINE)
    for m in r.finditer(text_blob):
        text_blob = text_blob.replace(m.group(0),
                                      '[[Note('+m.group(1)+')]]')

    # fix 8 - IncludePages(pagename,includeheader,includeblock)

    r = re.compile(r'\[\[IncludePages\((.+?),.+\)\]\]',re.IGNORECASE)
    for m in r.finditer(text_blob):
        page = m.group(1)
        page = page.replace('$','')
        page = page.replace('^','')
        text_blob = text_blob.replace(m.group(0),
                                      '[[IncludePages('+m.group(1)+',includeheader,includeblock)]]')

    # fix 9 - Strip additional args off include

    r = re.compile(r'\[\[Include\((.+?)\)\]\]',re.IGNORECASE)
    for m in r.finditer(text_blob):
        page = m.group(1)
        text_blob = text_blob.replace(m.group(0),
                                      '[[Include('+m.group(1)+')]]')


    # fix 10 - Standardize case of stop and nbsp macros

    text_blob = text_blob.replace('[[stop]]','[[Stop]]')
    text_blob = text_blob.replace('[[nbsp]]','[[Nbsp]]')
    

    return text_blob


# allpages
# conversion notes:  if the page text contains a link to a user page,
#                    update that link to Users/<username>.  
#                    if the page is a user page, change its name 
#                    Users/<username> as well.
#

def allpages(pgc,myc,users):

    print "Starting allpages"
    pgc.execute("""SELECT * FROM allpages ORDER BY name, edittime""");
    rows = pgc.fetchall()

    count = 0
    current_page = ''
    version = 0
    for row in rows :
        # if we have a new name, reset the version counter
        name = row[0]
        if (current_page == name):
            version += 1
        else:
            current_page = name
            version = 1

        # look up the username from the id/name dict
        if users.has_key(row[3]):
            username = users[row[3]]
        else:
            username = ''

        # get rid of the decimal part of the time
        edittime = int(row[2])

        # we may need to decode the blob(?)
        text_blob = str(row[1])
        #text_blob.decode("latin1")

        # convert the page text
        text_blob = page_conversions(text_blob)

        propercased_name = row[7]

        sql = "INSERT INTO wiki VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
        try:
            myc.execute( sql, (propercased_name,version,edittime,username,
                               row[6],text_blob,row[5],0))
        except:
            print "Integrity Error for %s" % propercased_name
            continue
        
        count += 1

    mydb.commit()
    print "Finished %d rows of allPages" % count

# allpagesfix
# conversion notes:  some of the propercase names are not
#                    in the proper case.  assume the latest version
#                    is canonical and update the db with that name
#

def allpagesfix(myc):

    print "Starting allpagesfix"
    myc.execute("""SELECT name, max(version) AS version FROM wiki
                   GROUP BY name""");
    rows = myc.fetchall()

    count = 0
    current_page = ''
    version = 0
    for row in rows :
        sql = """SELECT name FROM wiki WHERE name = %s AND version = %s"""
        myc.execute(sql,(row[0],row[1]))
        namerow = myc.fetchone()
        sql = "UPDATE wiki SET name = %s WHERE name = %s"
        try:
            myc.execute( sql, (namerow[0],namerow[0]))
        except:
            print "Integrity Error for %s" % namerow[0]
            continue
        
        count += 1

    mydb.commit()
    print "Finished %d rows of allPagesfix" % count


# files
# conversion notes:
#       sycamore allows duplicate filenames (same except for case)
#       they have to be removed before conversion
#

def files(pgc,myc,users):

    print "Starting files"

    pgc.execute("""SELECT * FROM files""");
    count = 0
    while (1):
        row = pgc.fetchone()
        if row == None:
            break
        
        # create the file
        attached_to_pagename = row[6]
        file_blob = str(row[1])
        file_blob.decode('latin1')
        
        path = ATTACHMENTS+'/'+unicode_quote(attached_to_pagename)
        if not os.access(path, os.F_OK):
            os.makedirs(path)
        filename = path+'/'+row[0]
        outfile = open(filename,'w')
        outfile.write(file_blob)
        outfile.close()
        print "Wrote %s \n" % filename

        # insert into database
        upload_time = int(row[2])
        if users.has_key(row[3]):
            username = users[row[3]]
        else:
            username = ''
        
        sql = "INSERT INTO attachment VALUES ('wiki',%s,%s,%s,%s,%s,%s,%s)"
        try:
            myc.execute(sql,(attached_to_pagename,
                             row[0],
                             len(file_blob),
                             upload_time,
                             '',
                             username,
                             row[5]))
        except:
            print "Error inserting "+row[0]+"\n"
            continue
        count += 1

    mydb.commit()
    print "Finished %d rows of files" % count

# users
# conversion notes:
#     convert userid, email, password and when joined
#     
#

def users(pgc,myc):

    print "Starting users"
    pgc.execute("""SELECT * FROM users """);
    rows = pgc.fetchall()

    count = 0
    for row in rows:
        print row[22]
        sql1 = "INSERT INTO session VALUES (%s,%s,%s)"
        sql2 = "INSERT INTO session_attribute VALUES (%s,%s,%s,%s)"
        try:
            myc.execute(sql1,(row[22],'1','0'))
            myc.execute(sql2,(row[22],'1','name',row[22]))
            myc.execute(sql2,(row[22],'1','email',row[2]))
            myc.execute(sql2,(row[22],'1','joindate',row[13]))
            myc.execute(sql2,(row[22],'1','password',':resetme'))
        except:
            print "Error inserting "+row[22]+"\n"
            continue
        count += 1
    mydb.commit()
    print "Finished %d rows of users" % count


# mappoints
# conversion notes:  move to new table, wikiaddress
#

def mappoints(pgc,myc):

    print "Starting mapPoints"
    pgc.execute("""SELECT * FROM mappoints""");
    rows = pgc.fetchall()

    count = 0
    for row in rows:
        # get rid of the decimal part of the time
        edittime = int(row[3])

        sql = "INSERT INTO wikiaddress VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        myc.execute(sql,(row[7],'',row[8],row[1],row[2],0,
                         edittime,row[4],row[5]))
        count += 1

    mydb.commit()
    print "Finished %d rows of mapPoints" % count


#####
# main


print "Starting conversion"

#  hard db connects for now

myc = mydb.cursor();
pgc = pgdb.cursor();

usernames = get_usernames(pgc)

allpages(pgc,myc,usernames)
allpagesfix(myc)

files(pgc,myc,usernames)
users(pgc,myc)
mappoints(pgc,myc)

mydb.close()
pgdb.close()

print "Conversion Finished" 

