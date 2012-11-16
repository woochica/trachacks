# -*- coding: utf-8 -*-

from datetime import datetime

from trac.ticket import ITicketChangeListener, Ticket
from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.util.datefmt import utc
try:
    from trac.util.datefmt import to_timestamp
except ImportError:
    from trac.util.datefmt import to_utimestamp as to_timestamp

from usermanual import *
try:
    from xmlrpc import *
except:
    pass


class WorkLogSetupParticipant(Component):
    implements(IEnvironmentSetupParticipant)

    db_version_key = None
    db_version = None
    db_installed_version = None
    
    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""
    def __init__(self):
        self.db_version_key = 'WorklogPlugin_Db_Version'
        self.db_version = 3
        self.db_installed_version = None

        # Initialise database schema version tracking.
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name=%s", (self.db_version_key,))
        try:
            self.db_installed_version = int(cursor.fetchone()[0])
        except:
            self.db_installed_version = 0
            try: 
                cursor.execute("INSERT INTO system (name,value) VALUES(%s,%s)",
                               (self.db_version_key, self.db_installed_version))
                db.commit()
            except Exception, e:
                db.rollback()
                raise e
    
    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)
            
    def system_needs_upgrade(self):
        return self.db_installed_version < self.db_version

    def do_db_upgrade(self, db):
        # Legacy support hack (supports upgrades from revisions r2495 or before)
        if self.db_installed_version == 0:
            try:
                
                db = self.env.get_db_cnx()
                cursor = db.cursor()
                cursor.execute('SELECT * FROM work_log LIMIT 1')
                # We've succeeded so we actually have version 1
                self.db_installed_version = 1
            except:
                db.rollback()
                self.db_installed_version = 0
        # End Legacy support hack

        # Do the staged updates
        cursor = db.cursor()
        try:
            # This var is to deal with a problem case with pgsql and the "user"
            # keyword. We need to skip over new installations but not upgrades
            # for other db backends.
            skip = False
            
            if self.db_installed_version < 1:
                print 'Creating work_log table'
                cursor.execute('CREATE TABLE work_log ('
                               'worker     TEXT,'
                               'ticket     INTEGER,'
                               'lastchange INTEGER,'
                               'starttime  INTEGER,'
                               'endtime    INTEGER'
                               ')')
                skip = True

            if self.db_installed_version < 2:
                print 'Updating work_log table (v2)'
                cursor.execute('ALTER TABLE work_log '
                               'ADD COLUMN comment TEXT')

            if self.db_installed_version < 3:
                print 'Updating work_log table (v3)'
                if not skip:
                    # This whole section is just to rename the "user" column to "worker"
                    # This column used to be created in step 1 above, but we
                    # can no longer do this in order to support pgsql.
                    # This step is skipped if step 1 was also run (e.g. new installs)
                    # The below seems to be the only way to rename (or drop) a column on sqlite *sigh*
                    cursor.execute('CREATE TABLE work_log_tmp ('
                                   'worker     TEXT,'
                                   'ticket     INTEGER,'
                                   'lastchange INTEGER,'
                                   'starttime  INTEGER,'
                                   'endtime    INTEGER,'
                                   'comment    TEXT'
                                   ')')
                    cursor.execute('INSERT INTO work_log_tmp (worker, ticket, lastchange, starttime, endtime, comment) '
                                   'SELECT user, ticket, lastchange, starttime, endtime, comment FROM work_log')
                    cursor.execute('DROP TABLE work_log')
                    cursor.execute('ALTER TABLE work_log_tmp RENAME TO work_log')

            #if self.db_installed_version < 4:
            #    print 'Updating work_log table (v4)'
            #    cursor.execute('...')
            
            # Updates complete, set the version
            cursor.execute("UPDATE system SET value=%s WHERE name=%s", 
                           (self.db_version, self.db_version_key))
            db.commit()
        except Exception, e:
            self.log.error("WorklogPlugin Exception: %s" % (e,));
            db.rollback()
            raise e

    def needs_user_man(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute('SELECT MAX(version) FROM wiki WHERE name=%s', (user_manual_wiki_title,))
            maxversion = int(cursor.fetchone()[0])
        except:
            db.rollback()
            maxversion = 0

        return maxversion < user_manual_version

    def do_user_man_update(self, db):
        cursor = db.cursor()
        try:
            when = to_timestamp(datetime.now(utc))
            cursor.execute('INSERT INTO wiki (name,version,time,author,ipnr,text,comment,readonly) '
                           'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                           (user_manual_wiki_title, user_manual_version, when,
                            'WorkLog Plugin', '127.0.0.1', user_manual_content,
                            '', 0))
            db.commit()
        except Exception, e:
            db.rollback()
            self.log.error("WorklogPlugin Exception: %s" % (e,));
        
    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.

        """
        return (self.system_needs_upgrade() \
                or self.needs_user_man())
            
    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        print "Worklog needs an upgrade"
        if self.system_needs_upgrade():
            print " * Upgrading Database"
            self.do_db_upgrade(db)
        if self.needs_user_man():
            print " * Upgrading usermanual"
            self.do_user_man_update(db)
        print "Done upgrading Worklog"

