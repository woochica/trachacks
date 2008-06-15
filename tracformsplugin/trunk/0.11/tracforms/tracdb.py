
from trac.core import Component, implements
from trac.env import IEnvironmentSetupParticipant
from datetime import datetime

class DBCursor(object):
    cursor = None

    def __init__(self, cursor, log):
        self.cursor = cursor
        self.log = log

    def __del__(self):
        if not self.cursor is not None:
            self.commit()

    def rollback(self):
        if self.cursor is not None:
            self.cursor.rollback()
            self.cursor = None

    def commit(self):
        if self.cursor is not None:
            self.cursor.commit()
            self.cursor = None

    def execute(self, sql, *params):
        self.log.debug('EXECUTING SQL:\n%s\n\t\%r' % (sql, params))
        self.cursor.execute(sql, params)
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

    def col(self, colno=0):
        def gen():
            for row in self:
                if colno >= len(row):
                    yield None
                else:
                    yield row[colno]
        return tuple(gen())

    def value(self, rowno=0, colno=0):
        row = self.row(rowno)
        if row is None or colno >= len(row):
            return None
        else:
            return row[colno]

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
                fn(cursor)
                self.set_installed_version(cursor, version)
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
            .value(default)

    def set_system_value(self, cursor, key, default=None):
        return self.get_cursor(cursor).execute(
            'UPDATE system SET value=%s WHERE name=%s', key)

    ###########################################################################
    #
    #   Cursor/Low Level Database Management
    #
    ###########################################################################
    def get_cursor(self, db_or_cursor=None):
        if db_or_cursor is None:
            db_or_cursor = self.env.get_db_cnx()
        if not isinstance(db_or_cursor, DBCursor):
            db_or_cursor = DBCursor(db_or_cursor.cursor(), self.log)
        return db_or_cursor

