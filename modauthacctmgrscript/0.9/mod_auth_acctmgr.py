# mod_auth_acctmgr module
# Copyright 2006 Noah Kantrowitz

from mod_python import apache
from trac.env import Environment

def authenhandler(req):
    pw = req.get_basic_auth_pw()
    user = req.user
    
    options = req.get_options()
    if 'TracEnv' not in options:
        print 'Must specify a Trac environment'
        return apache.HTTP_FORBIDDEN
    env_path = options['TracEnv']
    env = Environment(env_path)
    
    from acct_mgr.api import AccountManager

    if AccountManager(env).check_password(user, pw):
        return apache.OK
    else:
        return apache.HTTP_UNAUTHORIZED

