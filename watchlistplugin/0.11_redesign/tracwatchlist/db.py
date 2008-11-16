"""
 Watchlist Plugin for Trac
 Copyright (c) November 2008  Martin Scharrer <martin@scharrer-online.de>
 This is Free Software under the BSD license.
"""
from trac.core import *

from  trac.env         import  IEnvironmentSetupParticipant
from  trac.db          import  Table, Column, Index, DatabaseManager


wl_table = Table('watchlist')[
            Column('wluser'),
            Column('realm'),
            Column('resid') ]


class WatchlistDB(Component):
    """DB handler class for Trac WatchlistPlugin."""
    implements( IEnvironmentSetupParticipant )

    # IEnvironmentSetupParticipant methods:
    def _create_db_table(self, db=None):
        """ Create DB table if it not exists. """
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        db_connector, _ = DatabaseManager(self.env)._get_connector()

        for statement in db_connector.to_sql(wl_table):
            cursor.execute(statement)

        # Set database schema version.
        try:
            cursor.execute("INSERT INTO system (name, value) VALUES"
              " ('watchlist_version', '1')")
        except:
            pass
        return


    def _update_db_table(self, db=None):
        """ Update DB table. """
        self.env.log.debug("Updating DB table.")

        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute(
                "ALTER TABLE watchlist RENAME COLUMN user TO wluser;")
            cursor.execute(
                "ALTER TABLE watchlist RENAME COLUMN id   TO resid;")
        except Exception, e:
            raise TracError("Couldn't rename DB table columns: " + str(e))
        try:
            cursor.execute("INSERT INTO system (name, value) VALUES"
              " ('watchlist_version', '1')")
        except:
            pass
        return

    def environment_created(self):
        self._create_db_table()
        return

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("SELECT count(wluser),count(resid),count(realm) FROM watchlist;")
            count = cursor.fetchone()
            if count is None:
                return True
            cursor.execute("SELECT value FROM system WHERE name='watchlist_version';")
            (version,) = cursor.fetchone()
            if not version or int(version) < 1:
                return True
        except:
            return True
        return False

    def upgrade_environment(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("SELECT count(*) FROM watchlist;")
        except:
            self._create_db_table(db)
        else:
            try:
                cursor.execute("SELECT count(user),count(id),count(realm) FROM watchlist;")
            except:
                pass
            else:
                self._update_db_table(db)
        return

