#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, TracError, implements
from trac.db.api import DatabaseManager
from trac.env import IEnvironmentSetupParticipant

from tractags import db_default
from tractags.api import _


class TagSetup(Component):
    """Plugin setup and upgrade handler."""

    implements(IEnvironmentSetupParticipant)

    def __init__(self):
        db = DatabaseManager(self.env).get_connection()
        self.rollback_is_safe = False
        if self.get_schema_version(db):
            # We have a valid version, all transactions should succeed anyway.
            self.rollback_is_safe = False
            return
            
        # Preemptive check for rollback tolerance of read-only db connections.
        # This is required to avoid breaking `environment_needs_upgrade`,
        #   if the plugin uses intentional db transaction errors for the test.
        self.rollback_is_safe = True
        try:
            if hasattr(db, 'readonly'):
                db = DatabaseManager(self.env).get_connection(readonly=True)
                cursor = db.cursor()
                # Test needed for rollback on read-only connections.
                cursor.execute("SELECT COUNT(*) FROM system")
                cursor.fetchone()
                try:
                    db.rollback()
                except AttributeError:
                    # Avoid rollback on read-only connections.
                    self.rollback_is_safe = False
                    return
                # Test passed.
        except TracError, e:
            # Even older Trac - expect no constraints.
            return

    # IEnvironmentSetupParticipant methods

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        schema_ver = self.get_schema_version(db)
        if schema_ver == db_default.schema_version:
            return False
        elif schema_ver > db_default.schema_version:
            raise TracError(_("""A newer plugin version has been installed
                              before, but downgrading is unsupported"""))
        self.log.info("TracTags database schema version is %d, should be %d"
                      % (schema_ver, db_default.schema_version))
        return True

    def upgrade_environment(self, db):
        """Each schema version should have its own upgrade module, named
        upgrades/dbN.py, where 'N' is the version number (int).
        """
        db_mgr = DatabaseManager(self.env)
        schema_ver = self.get_schema_version(db)

        cursor = db.cursor()
        # Is this a new installation?
        if not schema_ver:
            # Perform a single-step install: Create plugin schema and
            # insert default data into the database.
            connector = db_mgr._get_connector()[0]
            for table in db_default.schema:
                for stmt in connector.to_sql(table):
                    cursor.execute(stmt)
            for table, cols, vals in db_default.get_data(db):
                cursor.executemany("INSERT INTO %s (%s) VALUES (%s)" % (table,
                                   ','.join(cols),
                                   ','.join(['%s' for c in cols])), vals)
        else:
            # Perform incremental upgrades.
            for i in range(schema_ver + 1, db_default.schema_version + 1):
                name  = 'db%i' % i
                try:
                    upgrades = __import__('tractags.upgrades', globals(),
                                          locals(), [name])
                    script = getattr(upgrades, name)
                except AttributeError:
                    raise TracError(_("""
                        No upgrade module for version %(num)i (%(version)s.py)
                        """, num=i, version=name))
                script.do_upgrade(self.env, i, cursor)
        cursor.execute("""
            UPDATE system
               SET value=%s
             WHERE name='tags_version'
            """, (db_default.schema_version,))
        self.log.info("Upgraded TracTags db schema from version %d to %d"
                      % (schema_ver, db_default.schema_version))
        db.commit()

    # Internal methods

    def get_schema_version(self, db=None):
        """Return the current schema version for this plugin."""
        if not db:
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT value
              FROM system
             WHERE name='tags_version'
        """)
        row = cursor.fetchone()
        #return row and int(row[0]) or 0
        # DEVEL: Remove __init__() and all code below after tags-0.7 release.

        if not (row and int(row[0]) > 2):
            # Care for pre-tags-0.7 installations.
            if self._db_table_exists(self.env, 'tags'):
                self.env.log.debug("TracTags needs to register schema version")
                return 2
            elif self._db_table_exists(self.env, 'wiki_namespace'):
                self.env.log.debug("TracTags needs to migrate old data")
                return 1
            else:
                # This is a new installation.
                return 0
        # The expected outcome for any up-to-date installation.
        return row and int(row[0]) or 0

    def _db_table_exists(self, env, table):
        # Using a separate connection per test minimises error side-effects.
        db = env.get_db_cnx()
        cursor = db.cursor()

        # Special handling for PostgreSQL Trac db backend.
        if env.config.get('trac', 'database').startswith('postgres'):
            cursor.execute("""
                SELECT relname
                  FROM pg_class
                 WHERE relname=%s 
            """ % table)
            if not cursor.fetchone():
                return True
            return False
        sql = "SELECT COUNT(*) FROM %s" % table
        try:
            cursor.execute(sql)
            cursor.fetchone()
            return True
        except Exception, e:
            if self.rollback_is_safe:
                db.rollback()
            return False
