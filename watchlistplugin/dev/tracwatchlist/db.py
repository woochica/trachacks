# -*- coding: utf-8 -*-
"""
= Watchlist Plugin for Trac =
Plugin Website:  http://trac-hacks.org/wiki/WatchlistPlugin
Trac website:    http://trac.edgewall.org/

Copyright (c) 2008-2010 by Martin Scharrer <martin@scharrer-online.de>
All rights reserved.

The i18n support was added by Steffen Hoffmann <hoff.st@web.de>.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For a copy of the GNU General Public License see
<http://www.gnu.org/licenses/>.

$Id$
"""

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2].strip('M'))
__date__     = ur"$Date$"[7:-2]

from  trac.core  import  *
from  trac.db    import  Table, Column, DatabaseManager
from  trac.env   import  IEnvironmentSetupParticipant


class WatchlistDataBaseUpgrader(Component):
    """DataBase module for the Trac WatchlistPlugin.
       Handles creation and upgrading of watchlist DB tables."""

    implements( IEnvironmentSetupParticipant )

    latest_version = 4

    watchlist_table = Table('watchlist', key=['wluser','realm','resid'])[
        Column('wluser'),
        Column('realm'),
        Column('resid'),
        Column('lastvisit', type='int64'),
    ]
    settings_table = Table('watchlist_settings', key=['wluser','name'])[
        Column('wluser'),
        Column('name'),
        Column('type'),
        Column('settings'),
    ]


    def environment_created(self):
        """Creates watchlist tables when a new Trac environment is created."""
        db = self.env.get_db_cnx()
        self.create_watchlist_table(db)
        self.create_settings_table(db)
        self.set_version(self.latest_version, db)
        self.upgrade_manual()
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
        # Commit now so that rollbacks do not affect any previous DB changes
        db.commit()
        old_version = self.get_version(db)
        self.upgrade_watchlist_table(old_version, self.latest_version, db)
        self.upgrade_settings_table (old_version, self.latest_version, db)
        self.set_version(self.latest_version, db)
        return


    def upgrade_watchlist_table(self, old_version, new_version, db=None):
        """Upgrades watchlist table to current version."""
        self.log.info("Attempting upgrade of watchlist table from v%i to v%i" % (old_version,new_version))
        db = db or self.env.get_db_cnx()
        if not self.watchlist_table_exists(db):
            self.create_watchlist_table(db)
            return
        if old_version == new_version:
            return
        try:
            upgrader = getattr(self, 'upgrade_watchlist_table_from_v%i_to_v%i' % (old_version, new_version))
        except AttributeError:
            raise TracError("Requested watchlist table version " + unicode(new_version) + " not supported for upgrade")

        upgrader(db)
        return


    def upgrade_settings_table(self, old_version, new_version, db=None):
        """Upgrades watchlist_settings table to current version."""
        self.log.info("Attempting upgrade of watchlist table from v%i to v%i" % (old_version,new_version))
        db = db or self.env.get_db_cnx()

        if not self.settings_table_exists(db):
            self.create_settings_table(db)
            return

        if old_version == new_version:
            return

        if old_version < 4:
            self.upgrade_settings_table_to_v4(db)
            old_version = 4
            if new_version == 4:
                return

        # Code for future versions > 4
        try:
            upgrader = getattr(self, 'upgrade_settings_table_from_v%i_to_v%i' % (old_version, new_version))
        except AttributeError:
            raise TracError("Requested settings table version " + unicode(new_version) + " not supported for upgrade")

        upgrader(db)
        raise NotImplemented


    def get_version(self, db=None):
        """Returns watchlist table version from system table or 0 if not present."""
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute("""
                SELECT value
                FROM system
                WHERE name='watchlist_version'
            """)
            valuelist = cursor.fetchone()
            return int(valuelist[0])
        except (AttributeError, TypeError):
            self.log.info("No value for 'watchlist_version' found in 'system' table")
            return 0
        except ValueError, e:
            self.log.error("Invalid value found for 'watchlist_version' found in system table: " + unicode(e))
            self.log.info("Value for 'watchlist_version' will be set to 0")
            self.set_version(0, db)
            return 0
        except Exception, e:
            db.rollback()
            self.log.error("Unknown error when trying to read 'watchlist_version' from 'system' table: " + unicode(e))
            self.log.info("Value for 'watchlist_version' will be set to 0")
            self.set_version(0, db)
            return 0


    def set_version(self, version, db=None):
        """Sets watchlist table version in the system table."""
        try:
            version = int(version)
        except ValueError:
            raise ValueError("Version must be an integer")
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute("""
                DELETE
                FROM system
                WHERE name='watchlist_version'
            """);
        except Exception as e:
            db.rollback()
            self.log.warn(unicode(e))
        try:
            cursor.execute("""
                INSERT
                INTO system (name,value)
                VALUES ('watchlist_version',%s)
            """, (unicode(version),) );
        except Exception as e:
            db.rollback()
            self.log.error("Could not set watchlist_version: " + unicode(e))
            raise
        db.commit()
        return


    def create_watchlist_table(self, db=None):
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        db_connector, _ = DatabaseManager(self.env)._get_connector()
        self.log.info("Creating 'watchlist' table in version " + unicode(self.latest_version))

        for statement in db_connector.to_sql(self.watchlist_table):
            cursor.execute(statement)
        db.commit()
        return


    def create_settings_table(self, db=None):
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        db_connector, _ = DatabaseManager(self.env)._get_connector()
        self.log.info("Creating 'watchlist_setting' table in version " + unicode(self.latest_version))

        for statement in db_connector.to_sql(self.settings_table):
            cursor.execute(statement)
        db.commit()
        return


    def watchlist_table_exists(self, db=None):
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute("SELECT count(*) FROM watchlist")
            return True
        except:
            db.rollback()
            self.log.info("No previous watchlist table found")
            return False


    def settings_table_exists(self, db=None):
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute("SELECT count(*) FROM watchlist_settings")
            return True
        except:
            db.rollback()
            self.log.info("No previous watchlist_settings table found")
            return False


    def upgrade_watchlist_table_from_v0_to_v4(self, db=None):
        self.upgrade_watchlist_table_to_v4('*', db)
        return


    def upgrade_watchlist_table_from_v1_to_v4(self, db=None):
        self.upgrade_watchlist_table_to_v4('*', db)
        return


    def upgrade_watchlist_table_from_v2_to_v4(self, db=None):
        """Upgrades watchlist table from v2 which has four columns.
           The forth was 'notify' which was dropped again quickly."""
        self.upgrade_watchlist_table_to_v4('wluser,realm,resid', db)
        return


    def upgrade_watchlist_table_from_v3_to_v4(self, db=None):
        self.upgrade_watchlist_table_to_v4('*', db)
        return


    def upgrade_watchlist_table_to_v4(self, selection, db=None):
        """Upgrade 'watchlist' table to v4. The data is copied into a temporary
           table and then back into the newly created table."""
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        db_connector, _ = DatabaseManager(self.env)._get_connector()

        # Temporary name for new watchlist table
        new_table = self.watchlist_table
        new_table.name = 'watchlist_new'

        # Delete new table if it should exists because of a aborted previous upgrade attempt
        try:
            cursor.execute("DROP TABLE watchlist_new")
        except:
            db.rollback()
            # Get new cursor
            cursor = db.cursor()

        # Create new table
        for statement in db_connector.to_sql(new_table):
            cursor.execute(statement)

        # Copy existing data to it
        cursor.execute("""
            INSERT
              INTO watchlist_new
            SELECT DISTINCT %s
              FROM watchlist
        """ % selection)

        # Delete only table
        cursor.execute("""
            DROP TABLE watchlist
        """)

        # Rename table
        cursor.execute("""
            ALTER TABLE watchlist_new
              RENAME TO watchlist
        """)

        db.commit()
        self.log.info("Upgraded 'watchlist' table to version 4")
        return


    def upgrade_settings_table_to_v4(self, db=None):
        """Upgrades 'watchlist_settings' table to v4.
           This table did not existed in v0-v2, so there is only v3
           to handle."""
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        db_connector, _ = DatabaseManager(self.env)._get_connector()

        # Delete new table if it should exists because of a aborted previous upgrade attempt
        try:
            cursor.execute("DROP TABLE watchlist_settings_new")
        except:
            db.rollback()
            # Get new cursor
            cursor = db.cursor()

        # Temporary name for new watchlist_settings table
        new_table = self.settings_table
        new_table.name = 'watchlist_settings_new'

        # Create new table
        for statement in db_connector.to_sql(new_table):
            cursor.execute(statement)

        # Copy existing data to it
        cursor.execute("""
            INSERT
              INTO watchlist_settings_new (wluser,settings)
            SELECT DISTINCT wluser,settings
              FROM watchlist_settings
        """)

        # Delete only table
        cursor.execute("""
            DROP TABLE watchlist_settings
        """)

        # Rename table
        cursor.execute("""
            ALTER TABLE watchlist_settings_new
              RENAME TO watchlist_settings
        """)

        # Set new columns to default value
        cursor.execute("""
            UPDATE watchlist_settings
               SET name='booloptions', type='ListOfBool'
        """)

        db.commit()
        self.log.info("Upgraded 'watchlist_settings' table to version 4")
        return

# EOF
