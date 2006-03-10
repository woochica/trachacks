# Copyright (C) 2006 Michael Kuehl <mkuehl@telaranrhiod.com>
# All rights reserved.
#
# This file is part of The Trac Peer Review Plugin
#
# The Trac Peer Review Plugin is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# The Trac Peer Review Plugin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with The Trac Peer Review Plugin; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from codereview.db import version as codereview_version, schema

class DiscussionInit(Component):
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
