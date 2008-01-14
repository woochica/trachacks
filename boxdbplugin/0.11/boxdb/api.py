# Created by  on 2008-01-02.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.

from trac.core import *
from trac.db import DatabaseManager
from trac.env import IEnvironmentSetupParticipant

from boxdb import db_default
from boxdb.compat import simplejson

class IDocumentPropertyRenderer(Interface):
    """Extension point interface for handling document properties."""

    def get_properties():
        """Return an iterable of property names this component will handle."""

    def render_property(name, value):
        """Return a value suitable for display."""


class BoxDBSystem(Component):
    """Core API implementation for BoxDB."""

    renderers = ExtensionPoint(IDocumentPropertyRenderer)

    implements(IEnvironmentSetupParticipant)

    def __init__(self):
        self.renderers_map = {}
        for renderer in self.renderers:
            for name in renderer.get_properties():
                self.renderers_map[name] = renderer

    # Public methods
    def get_documents(self, type=None, db=None):
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        
        if type is None:
            cursor.execute('SELECT DISTINCT name FROM boxdb')
        else:
            cursor.execute('SELECT DISTINCT name FROM boxdb WHERE ')
        
        for document, in cursor:
            yield document

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.found_db_version = 0
        self.upgrade_environment(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name=%s", (db_default.name,))
        value = cursor.fetchone()
        if not value:
            self.found_db_version = 0
            return True
        else:
            self.found_db_version = int(value[0])
            #self.log.debug('WeatherWidgetSystem: Found db version %s, current is %s' % (self.found_db_version, db_default.version))
            return self.found_db_version < db_default.version

    def upgrade_environment(self, db):
        db_manager, _ = DatabaseManager(self.env)._get_connector()
                
        # Insert the default table
        old_data = {} # {table_name: (col_names, [row, ...]), ...}
        cursor = db.cursor()
        if not self.found_db_version:
            cursor.execute("INSERT INTO system (name, value) VALUES (%s, %s)",(db_default.name, db_default.version))
        else:
            cursor.execute("UPDATE system SET value=%s WHERE name=%s",(db_default.version, db_default.name))
            for tbl in db_default.tables:
                try:
                    cursor.execute('SELECT * FROM %s'%tbl.name)
                    old_data[tbl.name] = ([d[0] for d in cursor.description], cursor.fetchall())
                    cursor.execute('DROP TABLE %s'%tbl.name)
                except Exception, e:
                    if 'OperationalError' not in e.__class__.__name__:
                        raise e # If it is an OperationalError, just move on to the next table
        
        
        for tbl in db_default.tables:
            for sql in db_manager.to_sql(tbl):
                cursor.execute(sql)
            
            # Try to reinsert any old data
            if tbl.name in old_data:
                data = old_data[tbl.name]
                sql = 'INSERT INTO %s (%s) VALUES (%s)' % \
                      (tbl.name, ','.join(data[0]), ','.join(['%s'] * len(data[0])))
                for row in data[1]:
                    try:
                        cursor.execute(sql, row)
                    except Exception, e:
                        if 'OperationalError' not in e.__class__.__name__:
                            raise e
