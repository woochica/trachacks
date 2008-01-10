import re
import dbhelper
from webui import *

from trac.core import *
from trac.env import IEnvironmentSetupParticipant

dbversion = 1
dbkey = 'EstimatorPluginDbVersion'


class EstimatorSetupParticipant(Component):
    """ Makes sure our database is what we expect """
    implements(IEnvironmentSetupParticipant)
    def __init__(self):
        # Setup logging
        dbhelper.env = self.env
        dbhelper.mylog = self.log

    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.
        """
        ver = dbhelper.get_system_value(dbkey)
        ans = (not ver) or (ver < dbversion)
        self.log.debug('Estimator needs upgrade? %s [installed version:%s  pluginversion:%s '%(ans, ver, dbversion))
        return ans

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        success = True
        ver = dbhelper.get_system_value(dbkey)
        self.log.debug('Estimator about to upgrade from ver:%s' % ver)
        if ver < 1:
            self.log.debug('Creating Estimate and Estimate_Line_Item tables (Version 1)')
            success &= dbhelper.execute_in_trans(
                ("""CREATE TABLE estimate(
                     id integer PRIMARY KEY,
                     rate DECIMAL,
                     variability DECIMAL,
                     communication DECIMAL,
                     tickets VARCHAR(512),
                     comment VARCHAR(8000)
                 )""",[]),
                ("""CREATE TABLE estimate_line_item(
                     id integer PRIMARY KEY,
                     estimate_id integer,
                     description VARCHAR(2048),
                     low DECIMAL,
                     high DECIMAL
                )""",[]))
        # SHOULD BE LAST IN THIS FUNCTION
        if success:
            dbhelper.set_system_value(dbkey, dbversion)
    
