# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Mikael Relbe
# All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software. 
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
# ----------------------------------------------------------------------------

from trac.core import *
from trac.db import *
from trac.env import IEnvironmentSetupParticipant

# Last database schema version
last_db_version = 1

class TicketChangesetsInit(Component):
    """Initialise database and environment for plugin."""

    implements(IEnvironmentSetupParticipant)

    # IEnvironmentSetupParticipant.
    def environment_created(self):
        # Initialise a created environment.
        @self.env.with_transaction()
        def do_create(db):
            self.upgrade_environment(db)

    def environment_needs_upgrade(self, db):
        # Is database up to date?
        return self._get_db_version(db) != last_db_version

    def upgrade_environment(self, db):
        # Get current database schema version.
        db_version = self._get_db_version(db)

        # Perform incremental upgrades.
        for I in range(db_version + 1, last_db_version + 1):
            script_name  = 'db%i' % I
            module = __import__('ticketchangesets.db.%s' % script_name,
                                globals(), locals(), ['do_upgrade'])
            module.do_upgrade(self.env, db)
            self.env.log.debug('ticketchangesets: Environment upgraded '
                               'to version %d' % I)

    def _get_db_version(self, db):
        if not db:
            db = self.env.get_read_db()
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE "
                       "name='ticket_changesets_version'")
        row = cursor.fetchone()
        return row and int(row[0]) or 0
