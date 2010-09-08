#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

# if you want to test this script, set this True:
#   then it won't send any mails, just it'll print out the produced html and text
test = False
#test = True

#which kind of db is Trac using?
mysql = False
pgsql = True
sqlite = False

# for mysql/pgsql:
dbhost="localhost"
dbuser="database_user"
dbpwd="database_password"
dbtrac="database_of_trac"
#or for sqlite:
sqlitedb='database_file_of_trac.ext'
#or if your db is in memory:
#sqlitedb=':memory:'

# the url to the trac (notice the slash at the end):
trac_url='http://path/to/your/trac/'
# the default domain, where the users reside
#  ie: if no email address is stored for them, username@domain.tld will be used
to_domain="@domain.tld"

# importing the appropriate database connector
#   (you should install one, if you want to use ;)
#    or you can use an uniform layer, like sqlalchemy)
if mysql:
    import MySQLdb
if pgsql:
    import psycopg2
if sqlite:
    from pysqlite2 import dbapi2 as sqlite

import sys
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

db = None
cursor = None

try:
    if mysql:
        db = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpwd, db=dbtrac)
    if pgsql:
        db = psycopg2.connect("host='"+ dbhost +"' user='" + dbuser + "' password='" + dbpwd + "' dbname='" + dbtrac + "'")
    if sqlite:
        db = sqlite.connect(sqlitedb)
except:
    print "cannot connect to db"
    raise
    sys.exit(1)

cursor = db.cursor()

#I think MySQL needs '"' instead of "'" without any ';', 
# with more strict capitalization (doubling quotes mean a single quote ;) )
# so you'll have to put these queries into this format: 
# sql="""query""" or sql='"query"' like
# sql = '"SELECT owner FROM ticket WHERE status !=""closed""""'
# for postgresql simply use:
sql = "select owner from ticket where status != 'closed'"
cursor.execute(sql)
ticket_owners = cursor.fetchall()

owners = []
for owner in ticket_owners:
    # get string from this tuple:
    realowner = ''.join(owner)
    if realowner not in owners and owner is not None and realowner != '':
        owners.append(realowner)
    realowner = ''

for owner in owners:
    msg = ''
    realowner = ''
    realowner = ''.join(owner)
    
    sql = "select time,summary,owner,status,id from ticket where status != 'closed' "
    sql += "and owner = '" + realowner + "' order by time DESC;"
    cursor.execute(sql)
    tickets_for_one_owner = cursor.fetchall()

    sql = "select sid,name,value from session_attribute where sid = '" + realowner + "' and name = 'email'"
    cursor.execute(sql)
    mailaddresses = cursor.fetchall()
    to_addr = ''
    
    for mailaddr in mailaddresses:
        if mailaddr is not None:
            to_addr = mailaddr[2]

    if to_addr == '':
        to_addr = realowner + to_domain
    del mailaddresses

    #lets assemble some html code:
    msg = "<html>\n<head>"
    msg = msg + "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\"/>\n"
    msg = msg + "<html lang=\"hu-HU\">\n"
    msg = msg + "<style type=\"text/css\"> <!--\n"
    msg += "body {color: #000000; background-color: #E6E6FA; background-color: #E6E6FA; text-align: left; text-alignment: left; font: normal 12pt Arial,Helvetica,sans #000000;} \n"
    msg += "#maindiv: {position:absolute; margin: 0px auto 0px auto; width: 530px; padding: 0px 5px 0px 10px}\n"
    msg += ".ticketdiv {background-color:#F8F8FF; color: #000000; margin: 15px 15px 5px 15px; width:500px; padding: 0px; position:relative; text-alignment:justify; text-align:left; border: 1px solid #000080;}"
    msg += "#headtitle {font:bold 14pt Arial,Helvetica,sans; color: #04090A; margin: 0px; padding: 2px 20px 2px 20px;} \n"
    msg += ".headsubtitle {margin: 0px; padding: 5px 5px 3px 5px; background-color:#000080; color: #FfFfFf; font: bold 14pt Arial,Helvetica,sans;} \n"
    msg += ".hsurl {text-decoration:none; text-color: #F8F8FF; color: #F8F8FF;}"
    msg += ".hsurl:hover {text-decoration:none; text-color: #FFDEAD; color:#FFDEAD;}"
    msg += "#headsubsubtitle {font:bold 14pt Arial,Helvetica,sans;} \n"
    msg += ".paragraph {padding:0px 0px 2px 5px; margin: 5px auto 5px auto; font:normal 11pt Arial,Helvetica,sans;} \n"
    msg += ".urlticket {text-decoration:none; text-color: #FF4500; color:#FF4500; font: bold 13pt Arial,Helvetica,sans; margin: 0px; padding: 0px 5px 0px 5px;} \n"
    msg += ".urlticket:hover {text-decoration:none; text-color: #FF4500; color:#FF4500;} \n"
    msg += ".urlmailto {text-decoration:none; font: bold 12pt Arial,Helvetica,sans;} \n"
    msg += ".urltkt {text-decoration:none; font: bold 12pt Arial,Helvetica,sans; text-color: #8B2500; color:#8B2500;} \n"
    msg += ".urltkt:hover {text-color: #FF4500; color: #FF4500;}\n"
    msg += ".statusfont {font:bold 12pt Arial,Helvetica,sans; color:#F00000; line-spacing:1px;} \n"
    msg += ".line {width:65%; border-top: 1px dashed #f00; border-bottom: 1px solid #f00; border-left:none; border-right:none; color: #E6E6FA; background-color: #E6E6FA; height: 4px;} \n"
    msg = msg + "--> \n </style>"
    msg = msg + "</head>"
    msg = msg + "<body bgcolor=\"#E6E6FA\"> \n<div class=\"maindiv\"><h1 id=\"headtitle\">"
    msg = msg + "Report for open Tickets on Trac (" + trac_url + "/project/)</h1>\n"
    
    #ok, now get those tickets:
    ticketlist = ''
    detail = ''
    for tkt in tickets_for_one_owner:
        tkt_url = trac_url + "ticket/" +str(tkt[4])
        tkt_href = "<a href=\"" + tkt_url + "\" class=\"urlticket\"> #" + str(tkt[4]) + "</a>"
        ticketlist += tkt_href
        ticketlist += "  "
            
        detail = detail + "<div class=\"ticketdiv\"><h2 class=\"headsubtitle\">Ticket <a href=\"" + tkt_url + "\" class=\"hsurl\"> #" + str(tkt[4]) + "</a>" + "</h2><p class=\"paragraph\">\n"
        detail = detail + "&nbsp;&nbsp;created at " + str(time.strftime('%Y. %B %d. (%A) %H:%M:%S',time.gmtime(tkt[0])))
        if tkt[2] != None:
            detail = detail + "<br>\n&nbsp;&nbsp;assigned to " + realowner + "<br>\n"
        detail = detail + "&nbsp;&nbsp;Url: <a href=\"" + tkt_url + "\" class=\"urltkt\">" + tkt_url + " </a><br>\n"
        detail = detail + "&nbsp;&nbsp;status: <font class=\"statusfont\">" + tkt[3] + "</font><br>\n"
        detail = detail + "&nbsp;&nbsp;Summary: " + tkt[1] + "</p>\n</div>\n"
    
    #done, now build them together and print it or send a mail:
    msg = msg + "<br>\n <a href=\"mailto:" + to_addr + "\" class=\"urlmailto\">" + realowner + "</a>" + " has these tickets: <br><br>\n" 
    msg = msg + ticketlist
    msg = msg + "\n<h3 id=\"headsubsubtitle\">In Details:</a><br>\n <div class=\"container\">"
    msg = msg + detail 
    msg = msg + "\n<br><hr class=\"line\"><br>\n"
    msg = msg + "</div></div></body>\n</html>"
    
    if test:
        print msg
    else:
        txtmsg = "Report open Tickets on Trac \n"
        txtmsg += realowner + " has these tickets: " + ticketlist + "\n"
        txtmsg += " details in html mail..."
        
        mailmsg = MIMEMultipart('alternative')
        mailmsg['Subject'] = "Report open Tickets for " + realowner + " " + time.strftime('%Y. %B %d. (%A) %H:%M:%S',time.localtime(time.time()))
        mailmsg['From'] = 'originating_mailaddress@domain.tld'
        mailmsg['To'] = to_addr

        part1 = MIMEText(txtmsg, 'plain')
        part2 = MIMEText(msg, 'html', 'utf-8')
    
        mailmsg.attach(part1)
        mailmsg.attach(part2)
        
        s = smtplib.SMTP()
        s.connect()
        s.sendmail(mailmsg['From'], mailmsg['To'], mailmsg.as_string())
        s.close()
        del s
        del part1
        del part2
        del mailmsg
        del txtmsg
    del msg
    del detail

#now print out the recipients where we've sent those mails... 
#  (ok, I know I could do this inside the cycle, but where's the fun? :) )
print "Trac reminder sent for these recipients:"
realowner = ''
for owner in owners:
    realowner = ''.join(owner)
    print realowner


# exiting program:
if db is not None:
    cursor.close()
    db.close()
