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

    def __init__(self):
        self.perms = {                         # should we have defaults here?
           "table":self.env.config.get('dbauth', 'perms_table'),
           "envname": self.env.config.get('dbauth','perms_envname_field'),
           "username": self.env.config.get('dbauth','perms_username_field'),
           "groupname": self.env.config.get('dbauth','perms_groupname_field')}

    def get_permission_groups(self, username):
        groups = ['anonymous']
        if username == 'Anonymous':
            return groups
        
        envname = get_envname(self.env)
        db = get_db(self.env)
        cursor = db.cursor()
        
        sql = "SELECT %(group)s " \
              "FROM %(table)s " \
              "WHERE (%(env)s=%%s or %(env)s='all') " \
              "  AND %(user)s=%%s " \
              "GROUP BY %(group)s " \
              "ORDER BY %(group)s" % \
              {'group' : self.perms['groupname'], 
               'table' : self.perms['table'],
               'env'   : self.perms['envname'], 
               'user'  : self.perms['username']}
        cursor.execute(sql, (envname,username))
                       
        # groupnames = cursor.fetchall()
        for groupname in cursor: #groupnames:
            groups.append(groupname[0])
        
        db.close()
        return groups
