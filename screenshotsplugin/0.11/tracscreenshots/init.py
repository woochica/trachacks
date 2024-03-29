# -*- coding: utf-8 -*-

# Standard includes.
import os, os.path

# Trac includes.
from trac.core import *
from trac.db import *
from trac.config import PathOption

# Trac interfaces.
from trac.env import IEnvironmentSetupParticipant

# Last screenshots database schema version.
last_db_version = 4

class ScreenshotsInit(Component):
    """
       Init component initialises database and environment for screenshots
       plugin.
    """
    implements(IEnvironmentSetupParticipant)

    # Configuration options.
    path = PathOption('screenshots', 'path', '../screenshots',
      doc = 'Path where to store uploaded screenshots.')

    # IEnvironmentSetupParticipanttr
    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()

        # Is database up to date?
        return (self._get_db_version(cursor) != last_db_version) or not \
          os.path.isdir(self.path)

    def upgrade_environment(self, db):
        cursor = db.cursor()

        # Create screenshots directory if not exists.
        if not os.path.isdir(self.path):
            os.mkdir(os.path.normpath(self.path))

        # Get current database schema version
        db_version = self._get_db_version(cursor)

        # Is this clean installation?
        if db_version == 0:
            # Perform single upgrade.
            module = __import__('tracscreenshots.db.db%s' % (last_db_version),
              globals(), locals(), ['do_upgrade'])
            module.do_upgrade(self.env, cursor, False)
        else:
            # Perform incremental upgrades
            for I in range(db_version + 1, last_db_version + 1):
                script_name  = 'db%i' % (I)
                module = __import__('tracscreenshots.db.%s' % (script_name),
                  globals(), locals(), ['do_upgrade'])
                module.do_upgrade(self.env, cursor, True)

    def _get_db_version(self, cursor):
        try:
            sql = ("""SELECT value
                      FROM system
                      WHERE name='screenshots_version'""")
            self.log.debug(sql)
            cursor.execute(sql)
            for row in cursor:
                return int(row[0])
            return 0
        except:
            return 0
