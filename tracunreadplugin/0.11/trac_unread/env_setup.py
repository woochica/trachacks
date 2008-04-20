# -*- coding: utf-8 -*-
from trac.env import IEnvironmentSetupParticipant
from trac.core import Component, implements

class TracUnreadSetupParticipant(Component):
    implements(IEnvironmentSetupParticipant)

    db_version_key = None
    db_version = None
    db_installed_version = None
    
    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""
    def __init__(self):
        # Setup logging
        self.db_version_key = 'TracUnread_Db_Version'
        self.db_version = 1
        self.db_installed_version = None

        # Initialise database schema version tracking.
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name=%s", (self.db_version_key,))
        try:
            self.db_installed_version = int(cursor.fetchone()[0])
        except:
            self.db_installed_version = 0
            cursor.execute("INSERT INTO system (name,value) VALUES(%s,%s)",
                           (self.db_version_key, self.db_installed_version))
            db.commit()
            db.close()
            print "Done"

    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.

        """
        return self.db_installed_version < self.db_version
            
    def upgrade_environment(self, db):
        
        print "TracUnread needs an upgrade"
        
        print "Upgrading Database"
        cur = db.cursor()
        if self.db_installed_version < 1:
            print "Creating trac_unread table"
            sql = """
            CREATE TABLE trac_unread (
            username text,
            last_read_on integer,
            type text,
            id text,
            UNIQUE (type, id, username)
            );
            """
            try:
                cur.execute(sql)
                
                # This statement block always goes at the end this method
                try:
                    cur.execute("UPDATE system SET value=%s WHERE name=%s",
                        (self.db_version, self.db_version_key))
                except:
                    cur.execute("INSERT INTO system (value, name) VALUES (%s, %s)",
                        (self.db_version, self.db_version_key))

                self.db_installed_version = self.db_version
                
                db.commit()
            except Exception, e:
                print "Upgrade failed\nSQL:\n%s\nError message: %s" % (sql, e)
                db.rollback();
