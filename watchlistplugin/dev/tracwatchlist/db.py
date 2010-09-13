# -*- coding: utf-8 -*-
"""
 Watchlist Plugin for Trac
 Copyright (c) 2008-2009  Martin Scharrer <martin@scharrer-online.de>
 This is Free Software under the BSD license.

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2].strip('M'))
__date__     = ur"$Date$"[7:-2]

from  trac.core  import  *
from  trac.db    import  Table, Column, Index, DatabaseManager
from  trac.env   import  IEnvironmentSetupParticipant
from  tracwatchlist.translation  import  _

__DB_VERSION__ = 3

class WatchlistDataBase(Component):
    """DataBase module for the Trac WatchlistPlugin.
       Handles creation and upgrading of watchlist DB tables."""

    implements( IEnvironmentSetupParticipant )

    ################ NEW CODE #########################
    # Will be overwritten by the old code until finished

    latest_version = 4

    watchlist_table = Table('watchlist', key=['wluser','realm','resid'])[
        Column('wluser'),
        Column('realm'),
        Column('resid'),
    ]
    settings_table = Table('watchlist_settings', key=['wluser','type'])[
        Column('wluser'),
        Column('type'),
        Column('settings'),
    ]

    def environment_created(self):
        """Creates watchlist tables when a new Trac environment is created."""
        db = self.env.get_db_cnx()
        self.create_watchlist_table(db)
        self.create_settings_table(db)
        self.set_version(latest_version, db)
        return

    def environment_needs_upgrade(self, db):
        """Tests if watchlist tables must be upgraded."""
        if not self.watchlist_table_exists(db):
            return True
        if not self.settings_table_exists(db):
            return True
        version = self.get_version(db)
        if version < self.latest_version:
            return True
        elif version > self.latest_version:
            raise TracError("Watchlist DB table version newer than plug-in version")
        return False

    def upgrade_environment(self, db):
        """Upgrades all watchlist tables to current version."""
        old_version = self.get_version(db)
        self.upgrade_watchlist_table(old_version, self.lastest_version, db)
        self.upgrade_settings_table (old_version, self.lastest_version, db)
        self.set_version(latest_version, db)
        return

    def upgrade_watchlist_table(old_version, new_version, db=None):
        """Upgrades watchlist table to current version."""
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        if not self.watchlist_table_exists(db):
            self.create_watchlist_table(db)
            return
        try:
            upgrader = getattr(self, 'upgrade_watchlist_table_from_v%i_to_v%i' % (old_version, new_version))
        except AttributeError:
            raise TracError(
                _("Requested watchlist table version %(version)s not supported for upgrade.",
                version=new_version))

        upgrader(db)
        return

    def upgrade_settings_table(old_version, new_version, db=None):
        """Upgrades watchlist_settings table to current version."""
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        if not self.settings_table_exists(db):
            self.create_settings_table(db)
            return
        raise NotImplemented

    def get_version(self, db=None):
        """Returns watchlist table version from system table or 0 if not present."""
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT value
              FROM system
             WHERE name='watchlist_version'
        """)
        valuelist = cursor.fetchone()
        try:
            return int(valuelist[0])
        except AttributeError:
            self.log.info(
                _("No value for '%(entry)s' found in $(table)s table.",
                entry='watchlist_version', table='system'))
            return 0
        except ValueError, e:
            self.log.error(
                _("Invalid value found for '%(entry)s' found in $(table)s table: ",
                entry='watchlist_version', table='system') + unicode(e))
            self.log.info(
                _("Value for '%(entry)s' will be set to %(value)s.",
                entry='watchlist_version', table='system'))
            self.set_version(0, db)
            return 0

    def set_version(self, version, db=None):
        """Sets watchlist table version in the system table."""
        try:
            version = int(version)
        except ValueError:
            raise ValueError(_("Version must be an integer"))
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            DELETE
              FROM system
             WHERE name='watchlist_version'
        """);
        cursor.execute("""
            INSERT
              INTO system (name,value)
            VALUES ('watchlist_version',%s)
        """, (unicode(version),) );
        return


    def create_watchlist_table(self, db=None):
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        db_connector, _ = DatabaseManager(self.env)._get_connector()
        self.log.info(
            _("Creating '%(name)s' table in version %(version)s."),
            name='watchlist', version=unicode(self.latest_version))

        for statement in db_connector.to_sql(self.watchlist_table):
            cursor.execute(statement)
        return

    def create_settings_table(self, db=None):
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        db_connector, _ = DatabaseManager(self.env)._get_connector()
        self.log.info(
            _("Creating '%(name)s' table in version %(version)s."),
            name='watchlist_settings', version=unicode(self.latest_version))

        for statement in db_connector.to_sql(self.settings_table):
            cursor.execute(statement)
        return

    def watchlist_table_exists(self, db=None):
        raise NotImplemented

    def settings_table_exists(self, db=None):
        raise NotImplemented

    def upgrade_watchlist_table_from_v0_to_v4(self, db=None):
        self.upgrade_watchlist_table_from_v3_to_v4(db)
        return

    def upgrade_watchlist_table_from_v1_to_v4(self, db=None):
        self.upgrade_watchlist_table_from_v3_to_v4(db)
        return

    def upgrade_watchlist_table_from_v2_to_v4(self, db=None):
        """Upgrades watchlist table from v2 which has four columns."""
        raise NotImplemented

    def upgrade_watchlist_table_from_v3_to_v4(self, db=None):
        """Upgrades watchlist table from all versions with three columns."""
        raise NotImplemented

    ################ OLD CODE #########################

    # IEnvironmentSetupParticipant methods:
    def _create_db_table(self, db=None, name='watchlist'):
        """ Create DB table if it not exists. """
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        #cursor.log = self.env.log
        self.env.log.info("Creating table '%s' for WatchlistPlugin", (name,) )
        db_connector, _ = DatabaseManager(self.env)._get_connector()

        table = Table(name)[
                    Column('wluser'),
                    Column('realm'),
                    Column('resid'),
                ]

        for statement in db_connector.to_sql(table):
            cursor.execute(statement)

        # Set database schema version.
        if (name == 'watchlist'):
          self._create_db_table2(db)
          cursor.execute("UPDATE system SET value=%s WHERE name='watchlist_version'",
                (str(__DB_VERSION__),) )
        cursor.connection.commit()
        return

    def _create_db_table2(self, db=None):
        """ Create settings DB table if it not exists. """
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        #cursor.log = self.env.log
        db_connector, _ = DatabaseManager(self.env)._get_connector()
        self.env.log.info("Creating 'watchlist_settings' table")

        table = Table('watchlist_settings', key=['wluser',])[
                    Column('wluser'),
                    Column('settings'),
                ]

        for statement in db_connector.to_sql(table):
            cursor.execute(statement)

        cursor.connection.commit()
        return

    def environment_created(self):
        self._create_db_table()
        return


    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("SELECT count(wluser),count(resid),count(realm) FROM watchlist")
            count = cursor.fetchone()
            if count is None:
                self.env.log.info("Watchlist table format to old")
                return True
            cursor.execute("SELECT count(*) FROM watchlist_settings")
            count = cursor.fetchone()
            if count is None:
                self.env.log.info("Watchlist settings table not found")
                return True
            cursor.execute("SELECT value FROM system WHERE name='watchlist_version'")
            version = cursor.fetchone()
            if not version or int(version[0]) < __DB_VERSION__:
                self.env.log.info("Watchlist table version (%s) to old" % (version))
                return True
        except Exception, e:
            cursor.connection.rollback()
            self.env.log.info("Watchlist table needs to be upgraded: " + unicode(e))
            return True
        return False

    def upgrade_environment(self, db):
        cursor = db.cursor()
        version = 0
        # Ensure system entry exists:
        try:
          cursor.execute("SELECT value FROM system WHERE name='watchlist_version'")
          version = cursor.fetchone()
          if not version:
            raise Exception("No version entry in system table")
          version = int(version[0])
        except Exception, e:
          self.env.log.info("Creating system table entry for watchlist plugin: " + unicode(e))
          cursor.connection.rollback()
          cursor.execute("INSERT INTO system (name, value) VALUES ('watchlist_version', '0')")
          cursor.connection.commit()
          version = 0

        try:
            cursor.execute("SELECT count(*) FROM watchlist")
        except:
            self.env.log.info("No previous watchlist table found")
            cursor.connection.rollback()
            self._create_db_table(db)
            return

        try:
            cursor.execute("SELECT count(*) FROM watchlist_settings")
        except:
            self.env.log.info("No previous watchlist_settings table found")
            cursor.connection.rollback()
            self._create_db_table2(db)

        # Upgrade existing database
        self.env.log.info("Updating watchlist table")
        try:
            self.env.log.info("Old version: %d, new version: %d" % (int(version),int(__DB_VERSION__)))
        except:
            pass

        try:
            try:
              cursor.execute("DROP TABLE watchlist_new")
            except:
              pass #cursor.connection.rollback()
            self._create_db_table(db, 'watchlist_new')
            cursor = db.cursor()
            try: # from version 0
              cursor.execute("INSERT INTO watchlist_new (wluser, realm, resid) "
                             "SELECT user, realm, id FROM watchlist")
              self.env.log.info("Update from version 0")
            except: # from version 1
              self.env.log.info("Update from version 1")
              cursor.connection.rollback ()
              cursor = db.cursor()
              cursor.execute("INSERT INTO watchlist_new (wluser, realm, resid) "
                              "SELECT wluser, realm, resid FROM watchlist")
              cursor.connection.commit()

            self.env.log.info("Moving new table to old one")
            cursor.execute("DROP TABLE watchlist")
            cursor.execute("ALTER TABLE watchlist_new RENAME TO watchlist")
            cursor.execute("UPDATE system SET value=%s WHERE "
                           "name='watchlist_version'", (str(__DB_VERSION__),) )
            cursor.connection.commit()
        except Exception, e:
            cursor.connection.rollback ()
            self.env.log.info("Couldn't update DB: " + to_unicode(e))
            raise TracError("Couldn't update DB: " + to_unicode(e))
        return

