# Created by Noah Kantrowitz on 2007-12-14.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.
import socket
import time

from trac.core import *
from trac.wiki.macros import WikiMacroBase
from trac.config import IntOption
from trac.env import IEnvironmentSetupParticipant

import db_default

class ServerDownMacro(WikiMacroBase):
    """A macro to check if a server is online."""

    default_timeout = IntOption('serverdown', 'default_timeout', default=60,
                                doc='Default refresh timeout for the ServerDown macro')

    default_port = IntOption('serverdown', 'default_port', default=80,
                             doc='Default por for the ServerDown macro')

    implements(IEnvironmentSetupParticipant)

    def expand_macro(self, formatter, name, content):
        # Parse arguments
        args = [v.strip() for v in content.split(',')]
        if len(args) == 1:
            args.append(self.default_port)
        if len(args) == 2:
            args.append(self.default_timeout)
        host, port, timeout = args
        port = int(port)
        timeout = int(timeout)
        
        # Check for cached value
        now = int(time.time())
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute('SELECT ts, value FROM serverdown WHERE host=%s AND port=%s', (host, port))
        row = cursor.fetchone()
        if row is not None and now - int(row[0]) < timeout:
            # Cache still valid
            value = row[1]
        else:
            # Check for new value
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.connect((host, port))
                except socket.error, e:
                    if e[1] == 'Connection refused':
                        value = 'Offline'
                    elif e[0] == 7 or e[0] == 11001:
                        value = 'Host %s not found'%host
                    else:
                        raise
                else:
                    value = 'Online'
            finally:
                s.close()
            
            # Update the cache
            cursor.execute('UPDATE serverdown SET ts=%s, value=%s WHERE host=%s AND port=%s',
                           (now, value, host, port))
            if not cursor.rowcount:
                cursor.execute('INSERT INTO serverdown (ts, value, host, port) VALUES (%s, %s, %s, %s)',
                               (now, value, host, port))
            db.commit()
        
        # Output
        return value

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

