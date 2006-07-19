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


from trac.db import *

def get_db(env):
    """Return a database connection"""
    return CentralDatabaseManager(env).get_connection()

def get_envname(env):
    envroot = env.config.get('dbauth', 'envroot')
    try:
        if envroot[-1] != "/":
            envroot += "/"
    except:
        raise TracError("No 'envroot' set in global trac.ini")
    envname = env.path.replace(envroot, "")
    return envname

    
class CentralDatabaseManager(DatabaseManager):
    connection_uri = Option('dbauth', 'database', 'sqlite:db/trac.db',
        """Database connection
        [wiki:TracEnvironment#DatabaseConnectionStrings string] for this
        project""")
    