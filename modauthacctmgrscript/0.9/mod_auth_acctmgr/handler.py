# mod_auth_acctmgr module
# Copyright 2006 Noah Kantrowitz

from mod_python import apache
from trac.web.main import _open_environment
from trac.perm import PermissionSystem

acct_mgr = None

def _get_env(req):
    """Get the Environment object for a request."""
    # Find the env_path from the Apache config
    options = req.get_options()
    if 'TracEnv' not in options:
        req.log_error('mod_auth_acctmgr: Must specify a Trac environment')
        return None
    env_path = options['TracEnv']

    # Try loading the env from the global cache, add it it if needed
    return _open_environment(env_path)

def authenhandler(req):
    pw = req.get_basic_auth_pw()
    user = req.user
    
    env = _get_env(req)
    if env is None:
        return apache.HTTP_FORBIDDEN

    global acct_mgr
    if acct_mgr is None:
        from acct_mgr.api import AccountManager
        acct_mgr = AccountManager

    options = req.get_options()
    #if 'TracPerm' not in options:
    #    req.log_error('mod_auth_acctmgr: You must specify a permission')
    #    return apache.HTTP_FORBIDDEN
    perm = options.get('TracPerm')

    if acct_mgr(env).check_password(user, pw):
        if perm:
            user_perms = PermissionSystem(env).get_user_permissions(user)
            if not user_perms.get(perm):
                return apache.HTTP_FORBIDDEN
        return apache.OK
    else:
        return apache.HTTP_UNAUTHORIZED

def perms(req):
    user = req.user
    
    env = _get_env(req)
    if env is None:
        return apache.HTTP_FORBIDDEN
        
    options = req.get_options()
    if 'TracPerm' not in options:
        req.log_error('mod_auth_acctmgr: You must specify a permission')
        return apache.HTTP_FORBIDDEN
    perm = options['TracPerm']
    
    user_perms = PermissionSystem(self.env).get_user_permissions(user)
    if user_perms.get(perm):
        return apache.OK
    else:
        return apache.HTTP_FORBIDDEN
    
