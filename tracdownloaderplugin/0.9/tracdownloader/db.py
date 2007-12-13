# -*- coding: utf-8 -*-
#
# Author: Petr Škoda <pecast_cz@seznam.cz>
# All rights reserved.
#
# This software is licensed under GNU GPL. You can read  it at
# http://www.gnu.org/licenses/gpl-3.0.html
#

from trac.core import *
from trac.db import Table, Column, Index

class DownloaderDB:
    
    ##
    ## Downloader plug-in's database schema
    ##
    
    schema = [
        # Downloader
        Table('downloader_category', key='id')[
            Column('id', auto_increment=True),
            Column('name'),
            Column('notes'),
            Column('sort', type='int'),
            Column('timestamp', type='int'),
            Column('deleted', type='int')],
        Table('downloader_release', key=('id'))[
            Column('id', auto_increment=True),
            Column('category'),
            Column('name'),
            Column('notes'),
            Column('sort', type='int'),
            Column('timestamp', type='int'),
            Column('deleted', type='int')],
        Table('downloader_file', key=('id'))[
            Column('id', auto_increment=True),
            Column('release'),
            Column('name'),
            Column('notes'),
            Column('architecture'),
            Column('sort', type='int'),
            Column('timestamp', type='int'),
            Column('deleted', type='int')],
        Table('downloader_downloaded', key=('id'))[
            Column('id', auto_increment=True),
            Column('file', type='int'),
            Column('timestamp', type='int')],
        Table('downloader_downloaded_attributes', key=(['downloaded', 'name']))[
            Column('downloaded', type='int'),
            Column('name'),
            Column('value')],
    ]
    
    def __init__(self, env):
        self.env = env
    
    # IEnvironmentSetupPart methods
    
    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""

    def environment_created(self):
        """Called when a new Trac environment is created."""
        pass
    
    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        cursor = db.cursor()
        for table in self.schema:
            try:
                from trac.db import DatabaseManager
                db_connector, _ = DatabaseManager(self.env)._get_connector()
            except ImportError:
                db_connector = db.cnx
            for stmt in db_connector.to_sql(table):
                cursor.execute(stmt)
            
        self.env.log.info("Downloader plug-in DB was created.")
                
    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.
        """
        """
        Checks existence of Downloader plug-in's DB.
        NOTE that it checks only existence of the first table!
        """
        
        cursor = db.cursor()
        try:
            cursor.execute("SELECT 1 FROM downloader_category")
        except:
            self.env.log.info("Downloader plug-in DB does not exist.")
            return True
        
        return False