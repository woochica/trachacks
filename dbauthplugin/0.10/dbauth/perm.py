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

from dbauth.env import *

from trac.core import *
from trac.perm import IPermissionGroupProvider 
from trac.util import TracError

class DbAuthPermissionGroupProvider(Component):
    """
    Provides permission groups 'anonymous', and whatever is in trac_permissions table.
    """

    implements(IPermissionGroupProvider)

    def get_permission_groups(self, username):
        groups = ['anonymous']
        if username == 'Anonymous':
            return groups
        
        envname = get_envname(self.env)
        db = get_db(self.env)
        cursor = db.cursor()
        
        cursor.execute("SELECT groupname "
                       "FROM trac_permissions "
                       "WHERE (envname=%s or envname='all') "
                       "  AND username=%s "
                       "GROUP BY groupname "
                       "ORDER BY groupname", (envname,username))
                       
        # groupnames = cursor.fetchall()
        for groupname in cursor: #groupnames:
            groups.append(groupname[0])
        
        db.close()
        return groups
