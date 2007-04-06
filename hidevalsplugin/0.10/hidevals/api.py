# Created by Noah Kantrowitz on 2007-04-02.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor, IPermissionGroupProvider, PermissionSystem
from trac.config import ListOption

try:
    set = set
except NameError:
    from sets import Set as set

import db_default

class HideValsSystem(Component):
    """Database provider for the TracHideVals plugin."""

    group_providers = ExtensionPoint(IPermissionGroupProvider)
    
    dont_filter = ListOption('hidevals', 'dont_filter', 
                             doc='Ticket fields to ignore when filtering.')

    implements(IPermissionRequestor, IEnvironmentSetupParticipant)
    
    # Public methods
    def visible_fields(self, req, db=None):
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        
        groups = self._get_groups(req.authname)
        fields = {}
        for group in groups:
            cursor.execute('SELECT field, value FROM hidevals WHERE sid = %s', (group,))
            for f, v in cursor:
                fields.setdefault(f, []).append(v)
                
        return fields
        
    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'TICKET_HIDEVALS'

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
            #self.log.debug('HideValsSystem: Found db version %s, current is %s' % (self.found_db_version, db_default.version))
            return self.found_db_version < db_default.version
            
    def upgrade_environment(self, db):
        # 0.10 compatibility hack (thanks Alec)
        try:
            from trac.db import DatabaseManager
            db_manager, _ = DatabaseManager(self.env)._get_connector()
        except ImportError:
                db_manager = db
                
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
                            
    # Private methods
    def _get_groups(self, user):
        # Get initial subjects
        groups = set([user])
        for provider in self.group_providers:
            for group in provider.get_permission_groups(user):
                groups.add(group)

        perms = PermissionSystem(self.env).get_all_permissions()
        repeat = True
        while repeat:
            repeat = False
            for subject, action in perms:
                if subject in groups and action.islower() and action not in groups:
                    groups.add(action)
                    repeat = True 

        return groups