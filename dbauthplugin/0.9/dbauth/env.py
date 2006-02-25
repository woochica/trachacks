# -*- coding: iso8859-1 -*-
#
# Copyright (C) 2005-2006 The Sankaty Group, Inc.
# Copyright (C) 2005-2006 Brad Anderson <brad@dsource.org>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Author: Brad Anderson <brad@dsource.org>

# for 0.10 and higher
#from trac.db.sqlite_backend import *

# for 0.9.x branch
from trac.db import SQLiteConnection

def get_db(env):
    """Return a database connection"""
    path = env.config.get('central', 'database')
    return SQLiteConnection(path)

def get_envname(env):
    envroot = env.config.get('central', 'envroot')
    if envroot[-1] != "/":
        envroot += "/"
    envname = env.path.replace(envroot, "")
    return envname

    