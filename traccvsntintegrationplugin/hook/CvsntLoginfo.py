# This program is free software; you can redistribute and/or modify it
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.


import os
import sqlite3
import sys
import time

class CvsntLoginfo():
    def __init__(self, config):
        self.config = config
        self.argv = []
        self.path = ''
        self.user = ''
        self.datetime = time.time()
        self.lines = []
        self.nfiles = 0
        self.filenames = []
        self.newrevs = []
        self.oldrevs = []
        self.log_message = ''
        self.newkey = -1


    def get_raw_info_from_hook(self):
        self.argv = sys.argv
        self.lines = []
        while True:
	        try: 
		        nextline = raw_input()
		        self.lines.append(nextline)
	        except EOFError: 
		        break
		    
		    
    def get_raw_info_from_db(self, callNo):
        self.datetime = 0.0
        self.lines = []
        self.argv = []
        
        db_connection = sqlite3.connect(self.config.call_db) 
        db_cursor = db_connection.cursor() 
        
        strselect='SELECT id, datetime FROM LOGINFO_CALLS WHERE id=' + repr(callNo)
        db_cursor.execute(strselect)    
        loginfoCallsRow = db_cursor.fetchone()
        self.datetime = loginfoCallsRow[1]
        
        strselect='SELECT loginfoID, _index, argv_index FROM LOGINFO_CALLS_ARGV WHERE loginfoID=' + repr(callNo)
        db_cursor.execute(strselect)    
        loginfoCallsRows = db_cursor.fetchall()        
        for row in loginfoCallsRows:
            self.argv.append(row[2])

        strselect='SELECT loginfoID, _index, line_index FROM LOGINFO_CALLS_STDOUT WHERE loginfoID=' + repr(callNo)
        db_cursor.execute(strselect)    
        loginfoCallsRows = db_cursor.fetchall()        
        for row in loginfoCallsRows:
            self.lines.append(row[2])
        
        db_connection.close()
    
    
    def get_loginfo_from_argv(self):
        self.user = self.argv[2]
        #argv[1] contains the folder relative to the folder followed by triplets filename,revision_new,revision_old
        argv1split = self.argv[1].split() 
        #handle whitespaces in file names 
        _argv1split = []
        _argv1split_tmp = ''
        for i in range(0, len(argv1split)):
            _argv1split_tmp = _argv1split_tmp + argv1split[i]
            if _argv1split_tmp.endswith('\\'):
                l = len(_argv1split_tmp)
                _argv1split_tmp = _argv1split_tmp[:l-1] + ' '
            else:
                _argv1split.append(_argv1split_tmp)
                _argv1split_tmp = ''
        self.nfiles = len(_argv1split)-1
        self.files = []
        self.newrevs = []
        self.oldrevs = []
        for i in range(1, self.nfiles+1):
            s = _argv1split[i].rsplit(',',2)
            self.files.append(s[0]) 
            self.newrevs.append(s[1])
            self.oldrevs.append(s[2])


    class ParseState:
        GET_PATH=0
        SKIP_DIRECTORY=1
        SKIP_FILES=2
        GET_LOG_MESSAGE=3

    def get_loginfo_from_stdin(self):
        state = self.ParseState.GET_PATH        
        for nextline in self.lines:
            strUpdateOfRepos = 'Update of ' + self.config.repos + '/';

            if state == self.ParseState.GET_PATH and nextline.find(strUpdateOfRepos) == 0:
                self.path = nextline.lstrip(strUpdateOfRepos)
                state = self.ParseState.SKIP_DIRECTORY
            elif state == self.ParseState.SKIP_DIRECTORY and nextline.find('Modified Files:') == 0:
                state = self.ParseState.SKIP_FILES
            elif state == self.ParseState.SKIP_DIRECTORY and nextline.find('Added Files:') == 0:
                state = self.ParseState.SKIP_FILES
            elif state == self.ParseState.SKIP_DIRECTORY and nextline.find('Removed Files:') == 0:
                state = self.ParseState.SKIP_FILES
            elif state == self.ParseState.SKIP_FILES:
                if nextline.find('Log Message:') == 0:
                    state = self.ParseState.GET_LOG_MESSAGE
            elif state == self.ParseState.GET_LOG_MESSAGE:
               if self.log_message != '':
                   self.log_message += '\n'
               self.log_message += nextline
               

    def db_check_create_calls(self):
        db_connection = sqlite3.connect(self.config.call_db) 
        db_cursor = db_connection.cursor() 
        
        # loginfo calls table        
        try:     
            strcreate = 'CREATE TABLE LOGINFO_CALLS (id INTEGER PRIMARY KEY, datetime FLOAT);'
            db_cursor.execute(strcreate) 
        except sqlite3.OperationalError, msg:
            print msg
            
        # loginfo calls argv table        
        try:     
            strcreate = 'CREATE TABLE LOGINFO_CALLS_ARGV (loginfoID INTEGER, _index INTEGER, argv_index TEXT);'
            db_cursor.execute(strcreate) 
        except sqlite3.OperationalError, msg:
            print msg
        # indices on loginfo calls argv table        
        try:     
            strcreate = 'CREATE INDEX LOGINFO_CALLS_ARGV_ID ON LOGINFO_CALLS_ARGV (loginfoID);'
            db_cursor.execute(strcreate) 
        except sqlite3.OperationalError, msg:
            print msg

        # loginfo calls stdout table        
        try:     
            strcreate = 'CREATE TABLE LOGINFO_CALLS_STDOUT (loginfoID INTEGER, _index INTEGER, line_index TEXT);'
            db_cursor.execute(strcreate) 
        except sqlite3.OperationalError, msg:
            print msg            
        # indices on loginfo calls stdout table        
        try:     
            strcreate = 'CREATE INDEX LOGINFO_CALLS_STDOUT_ID ON LOGINFO_CALLS_STDOUT (loginfoID);'
            db_cursor.execute(strcreate) 
        except sqlite3.OperationalError, msg:
            print msg
            
        db_connection.commit()
        db_connection.close()
    
    
    def db_insert_call(self):
        db_connection = sqlite3.connect(self.config.call_db) 
        db_cursor = db_connection.cursor() 

        strinsert = 'INSERT INTO LOGINFO_CALLS VALUES(NULL, \'' + repr(self.datetime) + '\')'
        db_cursor.execute(strinsert)
        newkey = db_cursor.lastrowid
        for i in range(0, len(self.argv)):
            strinsert = 'INSERT INTO LOGINFO_CALLS_ARGV VALUES(' + repr(newkey) + ',' + repr(i) + ', \'' + self.argv[i] + '\')'
            db_cursor.execute(strinsert)
        for i in range(0, len(self.lines)):
            strinsert = 'INSERT INTO LOGINFO_CALLS_STDOUT VALUES(' + repr(newkey) + ',' + repr(i) + ', \'' + self.lines[i] + '\')'
            db_cursor.execute(strinsert)
                
        db_connection.commit()
        db_connection.close()

    
    def db_check_create_changeset(self):
        db_connection = sqlite3.connect(self.config.changeset_db) 
        db_cursor = db_connection.cursor() 

        # changeset table        
        try:     
            strcreate = 'CREATE TABLE CHANGESET (id INTEGER PRIMARY KEY, description TEXT, path TEXT, user TEXT, datetime FLOAT);'
            db_cursor.execute(strcreate) 
        except sqlite3.OperationalError, msg:
            print msg            
        # indices on changeset table        
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
            
        # changeset files table        
        try:     
            strcreate = 'CREATE TABLE CHANGESET_FILES (changesetID INTEGER, filename TEXT, oldrev TEXT, newrev TEXT);'
            db_cursor.execute(strcreate) 
        except sqlite3.OperationalError, msg:
            print msg
        # indices on changeset files table        
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

        db_connection.commit()
        db_connection.close()
        
        
    def db_insert_append_changeset(self):        
        self.newkey = -1
        key = -1
        
        db_connection = sqlite3.connect(self.config.changeset_db) 
        db_cursor = db_connection.cursor() 
        
        strselect='SELECT id, description, datetime FROM CHANGESET WHERE datetime>=' + repr(self.datetime-300) + ' AND description=\'' + self.log_message + '\''
        db_cursor.execute(strselect)    
        changesetRow = db_cursor.fetchone()

        if changesetRow is None:       
            strinsert = 'INSERT INTO CHANGESET VALUES(NULL, \'' + self.log_message + '\', \'' + self.path + '\', \'' + self.user + '\', \'' + repr(self.datetime) + '\')'
            db_cursor.execute(strinsert)
            self.newkey = db_cursor.lastrowid
            key = self.newkey
        else:
            key = changesetRow[0]
        
        for i in range(0, self.nfiles):
            strinsert = 'INSERT INTO CHANGESET_FILES VALUES(' + repr(key) + ', \'' + self.path + '/' + self.files[i] + '\', \'' + self.oldrevs[i] + '\', \'' + self.newrevs[i] + '\')'
            db_cursor.execute(strinsert)

        db_connection.commit()
        db_connection.close()
        
        
    def trac_insert_changeset(self):
        if self.newkey <> -1:
            cmdtrac = self.config.tracpath + '/trac-admin' + ' ' + self.config.tracprojfolder + ' changeset added  ' + self.config.tracprojname + ' ' + repr(self.newkey)
            os.system(cmdtrac) 
