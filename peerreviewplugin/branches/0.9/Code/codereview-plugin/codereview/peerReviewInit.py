#	
# Copyright (C) 2005-2006 Team5	
# All rights reserved.	
#	
# This software is licensed as described in the file COPYING.txt, which	
# you should have received as part of this distribution.	
#	
# Author: Team5
#

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from codereview.db import version as codereview_version, schema

class PeerReviewInit(Component):
    """ Initialise database and environment for codereview plugin """
    implements(IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant
    def environment_created(self):
        pass
    
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        # Database is up to date?
        try:
            cursor.execute("SELECT value FROM system WHERE name='codereview_version'")
            version = int(cursor.fetchone()[0])
            return version != codereview_version
        except:
            return True
        return False
    
    def upgrade_environment(self, db):
        cursor = db.cursor()
        # Initial table creation
        try:
            for table in schema:
                for stmt in db.to_sql(table):
                    cursor.execute(stmt)
            cursor.execute("INSERT INTO system VALUES ('codereview_version', %s)", (codereview_version,))
            cursor.execute("INSERT INTO system VALUES ('CodeReviewVoteThreshold', '0')")         
        except:
            pass
        db.commit()
