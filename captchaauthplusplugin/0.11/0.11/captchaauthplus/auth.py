"""
plugin for Trac to give anonymous users authenticated access
using a CAPTCHA
"""

# Plugin for trac 0.11

from componentdependencies import IRequireComponents


from skimpyGimpy import skimpyAPI

from trac.core import *
from trac.env import IEnvironmentSetupParticipant



from web_ui import ImageCaptcha


try: 
    from acct_mgr.api import AccountManager
    #from acct_mgr.web_ui import RegistrationModule
except:
    AccountManager = None

class AuthCaptchaPlus(Component):

    ### class data
    implements( 
               IEnvironmentSetupParticipant, 
               IRequireComponents
               )

    
    ### auxiliary methods for IEnvironmentSetupParticipant
    
    def system_needs_upgrade(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute("SELECT * FROM login_attempts")                    
        except:
            return True
        db.close()
        return False
        
    def do_db_upgrade(self):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            print 'Creating login_attempts table'
            cursor.execute('CREATE TABLE login_attempts ('
                           'ip               TEXT,'
                           'attempts         INTEGER,'
                           'timestamp        INTEGER'
                           ')')
            db.commit()
            db.close()
        except Exception, e:
            print 'Error creating login_attempts table %s' % e
            self.log.error("Login Capcha Plugin Exception: %s" % (e,));
            db.rollback()
    

    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""

    ### methods for IEnvironmentSetupParticipant

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
        return (self.system_needs_upgrade())

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        print 'Login Capcha Plugin needs an upgrade'
        print ' * Upgrading db'
        self.do_db_upgrade()
        print 'Done Upgrading'

    ### method for IRequireComponents
        
    def requires(self):
        """list of component classes that this component depends on"""
        return [ImageCaptcha]


    ### internal methods
        

    def realm(self, req):
        """
        returns the realm according to the request
        """
        path = req.path_info.strip('/').split('/')
        if not path:
            return
        # TODO: default handler ('/')
        return path[0]
