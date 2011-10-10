# This program is free software; you can redistribute and/or modify it
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.


# CVSNT plugin

import datetime
import os
import sqlite3

from trac.config import PathOption
from trac.core import *
from trac.util.datefmt import utc
from trac.versioncontrol.api import IRepositoryConnector, Repository, Changeset, Node


def _normalize_path(path):
    """Remove leading "/", except for the root."""
    return path and path.strip('/') or '/'


class CvsntRepositoryConnector(Component):
    implements(IRepositoryConnector)

    def __init__(self):
        self._version = "0.0"
        self._version_info = (0,0,0)

    def get_supported_types(self):
        yield ("cvsnt", 8)

    def get_repository(self, type, dir, params):
        repos = CvsntRepository(dir, params, self.log)
        repos.version_info = self._version_info
        return repos



class CvsntRepository(Repository):

    #no time to debug why this SH*T won't work ...  changeset_db_path = PathOption('cvsnt', 'changeset_db_path', doc='Path to changeset database created by the hook script')
    changeset_db_path = '/CVSROOT/changesets.db'

    def __init__(self, path, params, log):
        self.path = path
        Repository.__init__(self, path, params, log)

    def get_changeset(self, rev):
        rev = self.normalize_rev(rev)
        self.log.debug('get_changeset ' + repr(rev))

        self.log.debug('get_changeset ' + self.path)
        self.log.debug('get_changeset ' + self.changeset_db_path)
        database_name = os.path.normpath(self.path + '/' + self.changeset_db_path)
        self.log.debug('get_changeset ' + database_name)
        db_connection = sqlite3.connect(database_name) 
        db_cursor = db_connection.cursor() 
        strselect='SELECT id, description, path, user, datetime FROM CHANGESET WHERE id=' + repr(rev)
        db_cursor.execute(strselect)    
        changesetRow = db_cursor.fetchone() 
        strselect='SELECT changesetID, filename, oldrev, newrev FROM CHANGESET_FILES WHERE changesetID=' + repr(rev)
        db_cursor.execute(strselect)    
        changesetFilesRows = db_cursor.fetchall()

        desc = 'User: ' + changesetRow[3] + '\n'
        desc += 'Folder: ' +  changesetRow[2] + '\n'
        for changesetFilesRow in changesetFilesRows:
            desc += changesetFilesRow[1] + ' ' + changesetFilesRow[2] + ' -> ' + changesetFilesRow[3] + '\n'
        desc += 'Log message:\n' + changesetRow[1]  
        return CvsntChangeset(self, rev, desc, changesetRow[3], changesetRow[4], self.log)


    def get_oldest_rev(self):
        database_name = "c:/jeroen_cvs/CVSROOT/changesets.db"
        db_connection = sqlite3.connect(database_name) 
        db_cursor = db_connection.cursor() 
        strselect = 'select min(id) from CHANGESET'
        db_cursor.execute(strselect)            
        row = db_cursor.fetchone()
        if len(row) == 1:
            return row[0]
        return None
        
    def get_youngest_rev(self):
        database_name = "c:/jeroen_cvs/CVSROOT/changesets.db"
        db_connection = sqlite3.connect(database_name) 
        db_cursor = db_connection.cursor() 
        strselect = 'select max(id) from CHANGESET'
        db_cursor.execute(strselect)            
        row = db_cursor.fetchone()
        if len(row) == 1:
            return row[0]
        return None

    def next_rev(self, rev, path=''):
        rev = self.normalize_rev(rev)
        self.log.debug('previous_rev ' + repr(rev))

        database_name = "c:/jeroen_cvs/CVSROOT/changesets.db"
        db_connection = sqlite3.connect(database_name) 
        db_cursor = db_connection.cursor() 
        strselect = 'select min(id) from CHANGESET WHERE id > ' + repr(rev)
        db_cursor.execute(strselect)            
        row = db_cursor.fetchone()
        if len(row) == 1:
            self.log.debug('previous_rev return ' + repr(row[0]))
            return row[0]
        self.log.debug('previous_rev return NONE')
        return None
        
    def previous_rev(self, rev, path=''):
        rev = self.normalize_rev(rev)
        self.log.debug('previous_rev ' + repr(rev))

        database_name = "c:/jeroen_cvs/CVSROOT/changesets.db"
        db_connection = sqlite3.connect(database_name) 
        db_cursor = db_connection.cursor() 
        strselect = 'select max(id) from CHANGESET WHERE id < ' + repr(rev)
        db_cursor.execute(strselect)            
        row = db_cursor.fetchone()
        if len(row) == 1:
            self.log.debug('previous_rev return ' + repr(row[0]))
            return row[0]
        self.log.debug('previous_rev return NONE')
        return None

    def normalize_rev(self, rev):
        if rev is None: 
            rev = self.youngest_rev
        else:
            rev = int(rev)
        return rev

    def normalize_path(self, path):
        """Take any path specification and produce a path suitable for 
        the rest of the API
        """
        return _normalize_path(path)
        
    def get_node(self, path, rev=None):
        self.log.debug('get_node path=' +path + ' rev=' + repr(rev))
        return CvsntNode(self, path, rev, self.log)
        
    def rev_older_than(self, rev1, rev2):
	    return False

	    
    def close(self):
	    return None
	    
    #def is_viewable(self, perm):
    #   return False



class CvsntChangeset(Changeset):

    def __init__(self, repos, rev, desc, user, time, log):
        self.repos = repos
        self.rev = rev
        self.log = log
        Changeset.__init__(self, repos, rev, desc, user, datetime.datetime.fromtimestamp(time,utc))

    def get_changes(self):
        changes = []
        database_name = os.path.normpath(self.repos.path + '/' + self.repos.changeset_db_path)
        db_connection = sqlite3.connect(database_name) 
        db_cursor = db_connection.cursor() 
        strselect='SELECT changesetID, filename, oldrev, newrev FROM CHANGESET_FILES WHERE changesetID=' + repr(self.rev)
        self.log.debug('get_changes ' + strselect)
        db_cursor.execute(strselect)    
        changesetFilesRows = db_cursor.fetchall()
        self.log.debug(changesetFilesRows)
        for changesetFilesRow in changesetFilesRows:
            strselect='SELECT max(changesetID) FROM CHANGESET_FILES WHERE changesetID<' + repr(self.rev) + ' AND filename=\'' + changesetFilesRow[1] + '\''
            prevrev = -1
            db_cursor.execute(strselect)    
            rowFileWasLastChanged = db_cursor.fetchone()
            if len(rowFileWasLastChanged) == 1:
                prevrev = rowFileWasLastChanged[0]
            changes.append([changesetFilesRow[1], Node.FILE, Changeset.EDIT, changesetFilesRow[1], prevrev])
        return changes
        

class CvsntNode(Node):

    def __init__(self, repos, path, rev, log):
        self.repos = repos
        self.path = path
        self.rev = rev
        self.log = log
        self.kind = Node.DIRECTORY
        
    def get_history(self, limit=None):
        self.log.debug('get_history ' + repr(limit))
        his = []
        return his
        
    def get_content_length(self):
        return 0

    def get_properties(self):
        props = []
        return props

    def get_content_type(self):
        return None
        
    def get_content(self):
        return self
        
    def read(self):
        print('rrrrrrrrreeeeeeaaaaaddddddddd')
        result = '0'
        database_name = os.path.normpath(self.repos.path + '/' + self.repos.changeset_db_path)
        db_connection = sqlite3.connect(database_name) 
        db_cursor = db_connection.cursor() 
        if self.rev is None:
            strselect='SELECT min(oldrev) FROM CHANGESET_FILES WHERE filename =\'' + self.path + '\''
        else:
            strselect='SELECT newrev FROM CHANGESET_FILES WHERE changesetID=' + repr(self.rev) + ' AND filename =\'' + self.path + '\''
        self.log.debug('get_changes ' + strselect)
        db_cursor.execute(strselect)    
        changesetFileRows = db_cursor.fetchone()
        if len(changesetFileRows) == 1:
            result = changesetFileRows[0]
        print(result)
        return result