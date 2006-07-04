from trac.core import *
from trac.config import *
from trac.config import OrderedExtensionsOption
from trac.env import IEnvironmentSetupParticipant

from api import ISubscribable, ISubscriptionFilter
from util import *
from db_default import db_version, default_table

import os

class SubscriptionManager(Component):
    """A class that manages data subscriptions."""

    subscribables = ExtensionPoint(ISubscribable)
    subscribtion_filters = OrderedExtensionsOption('tracforge-client','filters',ISubscriptionFilter,
                               include_missing=False, doc="""Filters for recieved data.""")

    implements(IEnvironmentSetupParticipant)

    # Subscription accessors    
    def get_subscribers(self, type, db=None):
        """Get all envs that are subscribed to this env."""
        return self._get_rows(type, 1, db)
        
    def get_subscriptions(self, type, db=None):
        """Get all envs this env is subscribed to."""
        return self._get_rows(type, 0, db)
        
    def _get_rows(self, type, direction, db=None):
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute('SELECT env FROM tracforge_subscriptions WHERE type = %s AND direction = %s',(type,str(direction)))
        for row in cursor:
            yield row[0]
            
    def get_subscribables(self):
        for source in self.subscribables:
            for x in source.subscribable_types():
                yield x
        
    # Subscription mutators
    def subscribe_to(self, source, type):
        source_env = open_env(source)
        source_mgr = SubscriptionManager(source_env)

        self._change_subscription('add', source_env.path, type, 0)    
        source_mgr._change_subscription('add', self.env.path, type, 1)
        
    def unsubscribe_from(self, source, type):
        source_env = open_env(source)
        source_mgr = SubscriptionManager(source_env)
        
        self._change_subscription('delete', source_env.path, type, 0)
        source_mgr._change_subscription('delete', self.env.path, type, 1)

    def _change_subscription(self, action, env, type, direction):
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        if action == 'add':
            cursor.execute('INSERT INTO tracforge_subscriptions (env, type, direction) VALUES (%s,%s,%s)',(env, type, direction))
        elif action == 'delete':
            cursor.execute('DELETE FROM tracforge_subscriptions WHERE env = %s AND type = %s AND direction = %s',(env, type, direction))
        else:
            raise TracError, 'Unknown subscription operation'

        db.commit()

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.upgrade_environment(self.env.get_db_cnx())
        
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name = 'tracforge_subscriptions'")
        value = cursor.fetchone()
        if not value:
            self.found_db_version = None
            return True
        else:
            self.found_db_version = int(value[0])
            self.log.debug('SubscriptionManager: Found db version %s, current is %s' % (self.found_db_version, db_version))
            return self.found_db_version < db_version
        
    def upgrade_environment(self, db):
        # 0.10 compatibility hack (thanks Alec)
        try:
            from trac.db import DatabaseManager
            db_manager, _ = DatabaseManager(self.env)._get_connector()
        except ImportError:
            db_manager = db
    
        # Insert the default table
        cursor = db.cursor()
        if self.found_db_version == None:
            cursor.execute("INSERT INTO system (name, value) VALUES ('tracforge_subscriptions', %s)",(db_version,))
        else:
            cursor.execute("UPDATE system SET value = %s WHERE name = 'tracforge_subscriptions'",(db_version,))
            cursor.execute('DROP TABLE tracforge_subscriptions')
            
        for sql in db_manager.to_sql(default_table):
            cursor.execute(sql)
        db.commit()
