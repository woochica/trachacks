# -*- coding: utf-8 -*-

from trac.core import *
from trac.db import *
from trac.env import IEnvironmentSetupParticipant

# Last visit counter database shcema version
last_db_version = 1

class VisitCounterInit(Component):
    """
      Initialise database and environment for visit counter macro.
    """
    implements(IEnvironmentSetupParticipant)

    #
    # Public methods
    #

    # IEnvironmentSetupParticipant

    """
      Action when new Trac environment created.
    """
    def environment_created(self):
        pass

    """
      Retruns if database schema needs upgrade.
    """
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()

        # Is database up to date?
        return self._get_db_version(cursor) != last_db_version

    """
      Performs database schema upgrade.
    """
    def upgrade_environment(self, db):
        cursor = db.cursor()

        # Get current database schema version
        db_version = self._get_db_version(cursor)

        # Perform incremental upgrades
        for I in range(db_version + 1, last_db_version + 1):
            script_name  = 'db%i' % (I)
            try:
                module = __import__('visitcounter.db.%s' % (script_name),
                  globals(), locals(), ['do_upgrade'])
                module.do_upgrade(cursor)
            except:
                raise TracError('Error upgrading database to version %i' % I)

    #
    # Private methods
    #

    """
      Returns database schema version.
    """
    def _get_db_version(self, cursor):
        try:
            sql = "SELECT value FROM system WHERE name='visitcounter_version'"
            self.log.debug(sql)
            cursor.execute(sql)
            for row in cursor:
                return int(row[0])
            return 0
        except:
            return 0
