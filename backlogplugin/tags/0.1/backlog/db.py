'''
Created on Aug 21, 2009
@author: Bart Ogryczak
'''


from trac.core import *
from trac.db.schema import Table, Column
from trac.env import IEnvironmentSetupParticipant

__all__ = ['BacklogSetup']

# Database version identifier for upgrades.
db_version = 1

# Database schema
schema = [
    # Backlogs
    Table('backlog', key=('id'))[
        Column('id', type='int'),
        Column('name',unique=True)],
    #Tickets in backlogs
    Table('backlog_ticket', key=('bklg_id', 'tkt_id'))[
        Column('bklg_id', type='int'),        
        Column('tkt_id', type='int'),
        Column('tkt_order', type='int')],
]


def to_sql(env, table):
    """ Convenience function to get the to_sql for the active connector."""
    from trac.db.api import DatabaseManager
    dm = env.components[DatabaseManager]
    dc = dm._get_connector()[0]
    return dc.to_sql(table)

def create_tables(cursor, env):
    """ Creates the basic tables as defined by schema.
    using the active database connector. """
    for table in schema:
        for stmt in to_sql(env, table):
            cursor.execute(stmt)    
    populate_tables(cursor, env)
    
  
#just an hack until admin interface is done
def populate_tables(cursor, env):
    bls = ((1, 'Product and Community'),
            (2, 'Sales and Business Intelligence'),
            (3, 'Business Development'),
            (4, 'System Engineering'))
    cursor.executemany('INSERT INTO backlog (id, name) VALUES (%s, %s)',bls)
    
def add_custom_fields(env):
    config = env.config
    config.set('ticket-custom','backlog','backlog')
    config.set('ticket-custom','backlog.label','backlog')
    config.set('ticket-custom','hard_deadline1','text')
    config.set('ticket-custom','hard_deadline1.label','hard deadline')
    config.set('ticket-custom','hard_deadline2','text')
    config.set('ticket-custom','hard_deadline2.label','reason for hard deadline')
    config.save()
        
# Upgrades

pass

# Component that deals with database setup

class BacklogSetup(Component):
    """Component that deals with database setup and upgrades."""
    
    implements(IEnvironmentSetupParticipant)

    def environment_created(self):
        """Called when a new Trac environment is created."""
        pass

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        Returns `True` if upgrade is needed, `False` otherwise."""
        cursor = db.cursor()
        return self._get_version(cursor) != db_version

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade, but don't commit as
        that is done by the common upgrade procedure when all plugins are done."""
        cursor = db.cursor()
        if self._get_version(cursor) == 0:
           print "creating backlog tables"
           create_tables(cursor, self.env)           
           cursor.execute("INSERT into system values ('backlog_version', %s)",(db_version,))
           print "adding custom ticket fields"
           add_custom_fields(self.env) 
           
        else:
            # do upgrades here when we get to that...
            pass

    def _get_version(self, cursor):
        try:
            sql = "SELECT value FROM system WHERE name='backlog_version'"
            self.log.debug(sql)
            cursor.execute(sql)
            for row in cursor:
                return int(row[0])
            return 0
        except:
            return 0
