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
from trac.versioncontrol.api import IRepositoryConnector, Repository, Changeset



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
        return CvsntChangeset(self, rev, desc, changesetRow[3], changesetRow[4])


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
        rev = int(rev)
        return rev

    def is_viewable(self, perm):
        return False



class CvsntChangeset(Changeset):

    def __init__(self, repos, rev, desc, user, time):
        Changeset.__init__(self, repos, rev, desc, user, datetime.datetime.fromtimestamp(time,utc))
