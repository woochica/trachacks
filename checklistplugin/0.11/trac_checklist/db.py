#
#   db.py -- Database management and access methods.
#

from trac.core import Component, Interface, implements
from trac.env import IEnvironmentSetupParticipant
from datetime import datetime

class IChecklistDBObserver(Interface):
    def checklist_getDBVersion():
        "Returns the current database version managed by the component."

    def checklist_getValues(context):
        "Returns a list of (value, when, who) tuples for the context passed."

    def checklist_setValue(context, field, value, who):
        "Adds or updates a value for the context field specified."

class ChecklistDBComponent(Component):
    implements(IEnvironmentSetupParticipant, IChecklistDBObserver)

    # Default state for db.
    db = None

    # IEnvironmentSetupParticpant
    def environment_created(self):
        pass
    
    def environment_needs_upgrade(self, db):
        installed = self.getInstalledVersion()
        for version, fn in self.getSchemaFunctions():
            if version > installed:
                return True
        else:
            return False

    def upgrade_environment(self, db):
        installed = self.getInstalledVersion()
        for version, fn in self.getSchemaFunctions():
            if version > installed:
                self.log.info(
                    'Upgrading Checklist Plugin Schema to %s' % version)
                fn()
                self.setInstalledVersion(version)
                installed = version
                self.log.info('Upgrade to %s successful.' % version)

    # IChecklistDBObserver
    def checklist_getDBVersion(self):
        return self.getInstalledVersion()

    def checklist_getValues(self, context):
        result = dict((name, (value, when, who))
            for name, value, when, who in
            self.iterate("""
                SELECT  field, value, updated_when, updater
                FROM    checklist_value
                WHERE   context = %s
                """, context))
        self.log.debug('checklist_getValues(%r) = %r' % (context, result))
        return result

    def checklist_setValue(self, context, field, value, who):
        when = datetime.now().isoformat(':')
        self.log.debug('checklist_setValue(%r, %r, %r, %r, %r)' %
            (context, field, value, who, when))
        if self.getValue("""
            SELECT  COUNT(*)
            FROM    checklist_value
            WHERE   context = %s AND field = %s
            """, context, field):

            self.commit("""
                UPDATE  checklist_value
                SET     value = %s,
                        updated_when = %s,
                        updater = %s
                WHERE   context = %s
                    AND field = %s
                """, value, when, who, context, field)
        else:
            self.commit("""
                INSERT  INTO checklist_value(
                        context, field, value, updated_when, updater)
                VALUES  (%s, %s, %s, %s, %s)
                """, context, field, value, when, who)

    #
    # Schema management
    def getSchemaFunctions(self):
        fns = []
        for name in self.__dict__:
            if name.startswith('dbschema_'):
                self.log.warning(name)
                fns.append((long(name[9:]), getattr(self, name)))
        for cls in self.__class__.__mro__:
            for name in cls.__dict__:
                if name.startswith('dbschema_'):
                    self.log.warning(name)
                    fns.append((name[9:], getattr(self, name)))
        fns.sort()
        return tuple(fns)

    def getInstalledVersion(self):
        return self.getSystemValue('ChecklistDBVersion', -1)

    def setInstalledVersion(self, version):
        return self.setSystemValue('ChecklistDBVersion', version)

    def dbschema_2008_03_10_000(self):
        'Create the checklist value table.'
        self.execute("""
            CREATE TABLE checklist_value(
                context         VARCHAR(255) NOT NULL,
                field           VARCHAR(255) NOT NULL,
                value           text NOT NULL,
                updated_when    DATETIME NOT NULL,
                updater         VARCHAR(32) NOT NULL
                )
            """)
        self.execute("""
            CREATE INDEX checklist_value_idx 
            ON checklist_value(context, field)
            """)

    #
    # Methods to get and set system values.
    def getSystemValue(self, key, default=None):
        return self.getValue(
            "SELECT value FROM system WHERE name=%s", key, default=default)

    def setSystemValue(self, key, value):
        if self.getSystemValue(key):
            self.execute(
                "UPDATE system SET value=%s WHERE name=%s", key, value)
        else:
            self.execute(
                "INSERT INTO system(name, value) VALUES (%s, %s)", key, value)

    #
    # Low level database activities.
    def getValue(self, sql, *params, **kw):
        colno = kw.pop('col', 0)
        default = kw.pop('default', None)
        row = self.getRow(sql, *params)
        if row is not None:
            if colno < len(row):
                return row[colno]
            else:
                return default
        else:
            return default

    def getRow(self, sql, *params, **kw):
        rowno = kw.pop('row', 0)
        cursor = self.execute(sql, *params)
        while rowno > 0:
            cursor.fetchone()
            rowno -= 1
        return cursor.fetchone()

    def iterate(self, sql, *params, **kw):
        cursor = self.execute(sql, *params)
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield row

    def execute(self, sql, *params, **kw):
        self.log.debug('EXECUTING SQL:\n%s\n\t%r' % (sql, params))
        self.db = self.env.get_db_cnx()
        cursor = self.db.cursor()
        cursor.execute(sql, params)
        return cursor

    def rollback(self):
        self.db.rollback()

    def commit(self, sql=None, *params, **kw):
        if sql is not None:
            cursor = self.execute(sql, *params, **kw)
        self.db.commit()

