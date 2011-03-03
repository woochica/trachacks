
from trac.core import Component, implements
from trac.env import IEnvironmentSetupParticipant
from datetime import datetime
import os, sys

DEBUG_SQL = os.environ.get('DEBUG_SQL', False)

class DBCursor(object):
    cursor = None

    def __init__(self, db, log):
        self.db = db
        self.cursor = db.cursor()
        self.log = log
        # Please, please tell me there's a better way to do this...
        dbtypename = type(self.db.cnx).__name__.split('.')[-1]
        self.dbtype = (
            (dbtypename == 'MySQLConnection' and 'mysql') or
            (dbtypename == 'PostgreSQLConnection' and 'postgres') or
            'sqlite')

    def __del__(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()

    def commit(self):
        self.db.commit()

    def execute(self, sql, *params, **variants):
        if DEBUG_SQL:
            print >>sys.stderr, 'EXECUTING SQL:\n%s\n\t%r' % (sql, params)
        sql = variants.get(self.dbtype, sql)
        self.log.debug('EXECUTING SQL:\n%s\n\t%r' % (sql, params))
        try:
            self.cursor.execute(sql, params)
        except Exception, e:
            self.log.error('EXECUTING SQL:\n%s\n\t%r' % (sql, params))
            self.rollback()
            raise e
        return self

    def __iter__(self):
        while True:
            row = self.cursor.fetchone()
            if row is None:
                break
            else:
                yield row

    def row(self, rowno=0):
        if rowno > 0:
            self.fetchmany(rowno)
        return self.cursor.fetchone()

    @property
    def firstrow(self):
        return self.row(0)

    def col(self, colno=0):
        def gen():
            for row in self:
                if colno >= len(row):
                    yield None
                else:
                    yield row[colno]
        return tuple(gen())

    @property
    def firstcol(self):
        return self.col(0)

    def at(self, default=None, rowno=0, colno=0):
        row = self.row(rowno)
        if row is None or colno >= len(row):
            return default
        else:
            return row[colno]

    @property
    def value(self):
        return self.at(None, 0, 0)

    def __call__(self, sql, *args, **variants):
        return self.execute(sql, *args, **variants)

    def last_id(self, cursor, table, column='id'):
        return self.db.get_last_id(self, table, column)

    @property
    def lastrowid(self):
        return self.cursor.lastrowid

 
class DBComponent(Component):
    implements(IEnvironmentSetupParticipant)
    applySchema = False

    ###########################################################################
    #
    #   IEnvironmentSetupParticipant
    #
    ###########################################################################
    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        if not type(self).__dict__.get('applySchema', False):
            self.log.debug(
                'Not checking schema for "%s", since applyScheme is not '
                'defined or is False.' % type(self).__name__)
            return False
        cursor = self.get_cursor(db)
        installed = self.get_installed_version(cursor)
        for version, fn in self.get_schema_functions():
            if version > installed:
                self.log.debug(
                    '"%s" requires a schema upgrade.' % type(self).__name__)
                return True
        else:
            self.log.debug(
                '"%s" does not need a schema upgrade.' % type(self).__name__)
            return False

    def upgrade_environment(self, db):
        if not type(self).__dict__.get('applySchema', False):
            self.log.debug(
                'Not updating schema for "%s", since applyScheme is not '
                'defined or is False.' % type(self).__name__)
            return
        self.log.debug(
            'Upgrading schema for "%s".' % type(self).__name__)
        cursor = self.get_cursor(db)
        installed = self.get_installed_version(cursor)
        for version, fn in self.get_schema_functions():
            if version > installed:
                self.log.info(
                    'Upgrading TracForm Plugin Schema to %s' % version)
                self.log.info('- %s: %s' % (fn.__name__, fn.__doc__))
                fn(cursor)
                self.set_installed_version(cursor, version)
                cursor.commit()
                installed = version
                self.log.info('Upgrade to %s successful.' % version)

    ###########################################################################
    #
    #   Schema Management
    #
    ###########################################################################
    def get_installed_version(self, cursor):
        cursor = self.get_cursor(cursor)
        return self.get_system_value(
            cursor, type(self).__name__ + ':version', -1)

    def get_schema_functions(self, prefix='dbschema_'):
        fns = []
        for name in self.__dict__:
            if name.startswith(prefix):
                fns.append((name, getattr(self, name)))
        for cls in type(self).__mro__:
            for name in cls.__dict__:
                if name.startswith(prefix):
                    fns.append((name, getattr(self, name)))
        fns.sort()
        return tuple(fns)

    def set_installed_version(self, cursor, version):
        cursor = self.get_cursor(cursor)
        self.set_system_value(
            cursor, type(self).__name__ + ':version', version)

    ###########################################################################
    #
    #   System Value Management
    #
    ###########################################################################
    def get_system_value(self, cursor, key, default=None):
        return self.get_cursor(cursor).execute(
            'SELECT value FROM system WHERE name=%s', key) \
            .value

    def set_system_value(self, cursor, key, value):
        if self.get_system_value(cursor, key) is not None:
            return self.get_cursor(cursor).execute(
                'UPDATE system SET value=%s WHERE name=%s', value, key)
        else:
            return self.get_cursor(cursor).execute(
                'INSERT INTO system(name, value) VALUES(%s, %s)', key, value)

    ###########################################################################
    #
    #   Cursor/Low Level Database Management
    #
    ###########################################################################
    def get_cursor(self, db_or_cursor=None):
        if db_or_cursor is None:
            db_or_cursor = self.env.get_db_cnx()
        if not isinstance(db_or_cursor, DBCursor):
            db_or_cursor = DBCursor(db_or_cursor, self.log)
        return db_or_cursor

