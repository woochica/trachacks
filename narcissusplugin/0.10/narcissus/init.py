#
# Narcissus plugin for Trac
#
# Copyright (C) 2008 Kim Upton	
# All rights reserved.
#
# Parts of this class were modified from the peerreview plugin, Copyright (C) Team5
#

from settings import *
from trac.core import *
from trac.db import *
from trac.env import IEnvironmentSetupParticipant
import db_default

class NarcissusInit(Component):
    """ Initialise database and environment for narcissus plugin """
    implements(IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant
    def environment_created(self):
        self.found_db_version = 0
        self.upgrade_environment(self.env.get_db_cnx())
    
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name = 'narcissus_version'")
        value = cursor.fetchone()
        if not value:
            self.found_db_version = 0
            return True
        else:
            self.found_db_version = int(value[0])
            return self.found_db_version < db_default.version

    def upgrade_environment(self, db):
        # 0.10 compatibility hack (thanks Alec (apparently))
        try:
            from trac.db import DatabaseManager
            db_manager, _ = DatabaseManager(self.env)._get_connector()
        except ImportError:
            db_manager = db

        # Insert the default tables
        cursor = db.cursor()
        if not self.found_db_version:
            cursor.execute("INSERT INTO system (name, value) VALUES ('narcissus_version', %s)",(db_default.version,))
        else:
            cursor.execute("UPDATE system SET value = %s WHERE name = 'narcissus_version'",(db_default.version,))
            for tbl in db_default.tables:
                try:
                    cursor.execute('DROP TABLE %s'%tbl.name,)
                except:
                    pass

        for tbl in db_default.tables:
            for sql in db_manager.to_sql(tbl):
                cursor.execute(sql)
        
        # Insert default settings
        cursor.execute("INSERT INTO narcissus_settings VALUES ('resource', 'wiki')")
        cursor.execute("INSERT INTO narcissus_settings VALUES ('resource', 'svn')")
        cursor.execute("INSERT INTO narcissus_settings VALUES ('resource', 'ticket')")
        
        settings = NarcissusSettings(db)
        
        bounds = settings.DEFAULT_BOUNDS
        for b in bounds:
            for i, threshold in enumerate(bounds[b]):
                cursor.execute("INSERT INTO narcissus_bounds VALUES ('%s', %s, %s)" % (b, i + 1, threshold))
        
        credits = settings.DEFAULT_CREDITS
        for c in credits:
            cursor.execute("INSERT INTO narcissus_credits VALUES ('%s', %s)" % (c, credits[c]))