# This program is free software; you can redistribute and/or modify it
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.


import os
import sqlite3
import sys
from CvsntLoginfo import CvsntLoginfo

# edit these string constants to match your configuration
repos          = '/repositories_cvs'                   # cvsnt repository name
database_name  = 'c:/jeroen_cvs/CVSROOT/changesets.db' # path to new database file
tracpath       = 'c:/temp/trac/scripts'                # path where trac was installed
tracprojfolder = 'c:/temp/trac/test'                   # trac project folder
tracprojname   = 'test'                                # trac project name


# retrieve info from the cvsnt loginfo hook calling this script
loginfo = CvsntLoginfo(repos)
loginfo.get_loginfo_from_argv(sys.argv)
loginfo.get_loginfo_from_stdin()


# cvsnt has no changeset database so we create our own ...
db_connection = sqlite3.connect(database_name) 
db_cursor = db_connection.cursor() 

# create the tables if it's not yet there
createdb = True
if createdb:
    try:     
        strcreate = 'CREATE TABLE CHANGESET (id INTEGER PRIMARY KEY, description TEXT, path TEXT, user TEXT, datetime FLOAT);'
        db_cursor.execute(strcreate) 
    except sqlite3.OperationalError, msg:
        print msg
    try:     
        strcreate = 'CREATE INDEX CHANGESET_DESCRIPTION ON CHANGESET (description);'
        db_cursor.execute(strcreate) 
    except sqlite3.OperationalError, msg:
        print msg
    try:     
        strcreate = 'CREATE INDEX CHANGESET_DATETIME ON CHANGESET (datetime);'
        db_cursor.execute(strcreate) 
    except sqlite3.OperationalError, msg:
        print msg
    try:     
        strcreate = 'CREATE INDEX CHANGESET_DESCRIPTION_DATETIME ON CHANGESET (description, datetime);'
        db_cursor.execute(strcreate) 
    except sqlite3.OperationalError, msg:
        print msg
    try:     
        strcreate = 'CREATE TABLE CHANGESET_FILES (changesetID INTEGER, filename TEXT, oldrev TEXT, newrev TEXT);'
        db_cursor.execute(strcreate) 
    except sqlite3.OperationalError, msg:
        print msg
    try:     
        strcreate = 'CREATE INDEX CHANGESET_FILES_ID ON CHANGESET_FILES (changesetID);'
        db_cursor.execute(strcreate) 
    except sqlite3.OperationalError, msg:
        print msg
    try:     
        strcreate = 'CREATE INDEX CHANGESET_FILES_FILENAME ON CHANGESET_FILES (filename);'
        db_cursor.execute(strcreate) 
    except sqlite3.OperationalError, msg:
        print msg
    try:     
        strcreate = 'CREATE INDEX CHANGESET_FILES_ID_FILENAME ON CHANGESET_FILES (changesetID, filename);'
        db_cursor.execute(strcreate) 
    except sqlite3.OperationalError, msg:
        print msg

# insert a new record
try:     
    strinsert = 'INSERT INTO CHANGESET VALUES(NULL, \'' + loginfo.log_message + '\', \'' + loginfo.path + '\', \'' + loginfo.user + '\', \'' + repr(loginfo.datetime) + '\')'
    db_cursor.execute(strinsert)
    newkey = db_cursor.lastrowid
    for i in range(0, loginfo.nfiles):
        strinsert = 'INSERT INTO CHANGESET_FILES VALUES(' + repr(newkey) + ', \'' + loginfo.files[i] + '\', \'' + loginfo.oldrevs[i] + '\', \'' + loginfo.newrevs[i] + '\')'
        db_cursor.execute(strinsert)
    db_connection.commit()
    db_connection.close()
except sqlite3.OperationalError, msg:
    print msg


# now call trac (the cvsnt repository within trac will get the info from the record that we inserted above)
cmdtrac = tracpath + '/trac-admin' + ' ' + tracprojfolder + ' changeset added  ' + tracprojname + ' ' + repr(newkey)
print cmdtrac
os.system(cmdtrac) 


print "path: " + loginfo.path
print "user: " + loginfo.user
print "datetime: " + repr(loginfo.datetime)
print "files: "
for i in range(0, loginfo.nfiles):
    print loginfo.files[i] + ' ' + loginfo.oldrevs[i] + ' -> ' + loginfo.newrevs[i]
print "log message: " + loginfo.log_message