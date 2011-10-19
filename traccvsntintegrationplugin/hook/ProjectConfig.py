# This program is free software; you can redistribute and/or modify it
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.


import os
import sqlite3
import sys
import time

class ProjectConfig():
    def __init__(self):
        # edit these string constants to match your configuration
        self.repos          = '/repositories_cvs'                            # cvsnt repository name
        self.call_db        = 'c:/jeroen_cvs/CVSROOT/loginfo_hook_calls.db'  # path to new database file
        self.changeset_db   = 'c:/jeroen_cvs/CVSROOT/changesets.db'          # path to new database file
        self.tracpath       = 'c:/temp/trac/scripts'                         # path where trac was installed
        self.tracprojfolder = 'c:/temp/trac/test'                            # trac project folder
        self.tracprojname   = 'test'                                         # trac project name