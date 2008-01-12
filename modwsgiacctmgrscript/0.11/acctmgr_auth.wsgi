# -*- coding: utf-8 -*-
#
# mod_wsgi_acctmgr module
#
# Copyright (C) 2008 John Hampton <pacoapblo@pacopablo.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: John Hampton <pacopablo@pacopablo.com>
#
# Based on Noah Kantrowitz's ModAuthAccmgr Script:
# http://trac-hacks.org/wiki/ModAuthAcctmgrScript

# For mod_wsgi, configuration must be done inside the script itself.
# Modify the following values:
# ------------------------------
TRAC_ENV="/path/to/trac/env"
PYTHON_EGG_CACHE="/path/to/python/egg_cache"
# ------------------------------

import os, sys
os.environ['PYTHON_EGG_CACHE'] = PYTHON_EGG_CACHE

from trac.env import open_environment, Environment

acct_mgr = None

def check_password(environ, user, password):
    global acct_mgr, TRAC_ENV
    
    # Try loading the env from the global cache, addit it if needed
    env = open_environment(TRAC_ENV, use_cache=True)
    
    if acct_mgr is None:
        from acct_mgr.api import AccountManager
        acct_mgr = AccountManager

    if acct_mgr(env).check_password(user, password):
        return True
    else:
        return False

def groups_for_user(environ, user):
    return ['']
