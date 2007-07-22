from trac.core import *
from trac.env import IEnvironmentSetupParticipant

class GringottSetupParticipant(Component):
    implements(IEnvironmentSetupParticipant)
    
    version = 1
    installed_version = 0
    name = "gringott_plugin_version"

    def __init__(self):
        # Initialise database schema version tracking.
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT value FROM system WHERE name=%s',
                       (self.name,))
        try:
            self.installed_version = int(cursor.fetchone()[0])
        except:
            self.installed_version = 0
            cursor.execute('INSERT INTO system (name,value) VALUES(%s,%s)',
                           (self.name, self.installed_version))
            db.commit()
            db.close()

    def system_needs_upgrade(self):
        if self.installed_version < self.version:
            return True

        if not self.config.get('gringotts', 'key'):
            return True
        
        return False
        
    def do_db_upgrade(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            if self.installed_version < 1:
                cursor.execute("CREATE TABLE gringotts ("
                               "name       VARCHAR(255),"
                               "version    INTEGER,"
                               "time       INTEGER,"
                               "text       TEXT,"
                               "acl        TEXT,"
                               "UNIQUE(name,version))")
      
            #if self.installed_version < 2:
            #  cursor.execute("...")
    
            # Updates complete, set the version
            cursor.execute("UPDATE system SET value=%s WHERE name=%s", 
                           (self.version, self.name))
            db.commit()
            db.close()
    
        except Exception, e:
            self.log.error("Gringott Exception: %s" % (e,));
            db.rollback()

    def do_key_generate(self):
        if self.config.get('gringotts', 'key'):
            print '   existing key found - skipping'
            return
        
        import ezPyCrypto
        print '   Generating 2048-bit keypair - could take a while...'
        k = ezPyCrypto.key(2048)
        self.config.set('gringotts', 'key', k.exportKeyPrivate())
        self.config.save()

        k = ezPyCrypto.key(str(self.config.get('gringotts','key')))
        secret = 'Something noone should know'
        if secret == k.decString(k.encString(secret)):
            print '   Encryption test successful'
        print '   done.'

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)
    
    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.

        """
        return self.system_needs_upgrade()

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        print 'GringottPlugin needs an upgrade'
        print ' * Upgrading db'
        self.do_db_upgrade()
        print ' * Initialising Encryption'
        self.do_key_generate()
        print 'Done Upgrading'

