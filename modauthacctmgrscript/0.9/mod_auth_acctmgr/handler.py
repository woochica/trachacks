# mod_auth_acctmgr module
# Copyright 2006 Noah Kantrowitz

from mod_python import apache
from trac.env import Environment

envs = {}
acct_mgr = None

def authenhandler(req):
    global envs, acct_mgr
    pw = req.get_basic_auth_pw()
    user = req.user
    
    # Find the env_path from the Apache config
    options = req.get_options()
    if 'TracEnv' not in options:
        print 'Must specify a Trac environment'
        return apache.HTTP_FORBIDDEN
    env_path = options['TracEnv']

    # Try loading the env from the global cache, addit it if needed
    env = None
    if env_path not in envs:
        env = Environment(env_path)
        envs[env_path] = env
    else:
        env = envs[env_path]
    
    if acct_mgr is None:
        from acct_mgr.api import AccountManager
        acct_mgr = AccountManager

    if acct_mgr(env).check_password(user, pw):
        return apache.OK
    else:
        return apache.HTTP_UNAUTHORIZED

