from trac.core import *
from trac.web import IAuthenticator

class SSLAuthenticationPlugin(Component):
    implements(IAuthenticator)

    # IAuthenticator methods
    def authenticate(self, req):
        authname = None
        req.perm_user = None

        # If SSL_CLIENT_S_DN_Email is set (an e-mail address part of the SSL
        # client certificate), then use this to check the permission store with
        if 'SSL_CLIENT_S_DN_Email' in req.environ:
            req.perm_user = req.environ['SSL_CLIENT_S_DN_Email']

        # Check for the user's name (and possibly login-/permission-name as
        # well). First check for a name in an SSL client certicicate
        if 'SSL_CLIENT_S_DN_CN' in req.environ:
            authname = req.environ['SSL_CLIENT_S_DN_CN']
        # Use the e-mail address from the SSL client certificiate we found above
        elif req.perm_user:
            authname = req.perm_user

        return authname
