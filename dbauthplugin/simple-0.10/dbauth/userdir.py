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

from dbauth.auth import *

from trac.userdir import *


class DbAuthUserDirectory(Component):
    implements (IUserDirectory)

    def __init__(self):
        self.envname = get_envname(self.env)
        self.perms = {                         # should we have defaults here?
           "table":self.env.config.get('dbauth', 'perms_table'),
           "envname": self.env.config.get('dbauth','perms_envname_field'),
           "username": self.env.config.get('dbauth','perms_username_field'),
           "groupname": self.env.config.get('dbauth','perms_groupname_field')}

    # IUserDirectory methods

    def get_known_user_info(self, limit=None):
        cnx = get_db(self.env)
        cursor = cnx.cursor()
        sql = "SELECT %s " \
              "FROM %s " \
              "WHERE (%s=%%s or %s='all') " \
              "ORDER BY %s" % \
              (self.perms['username'], self.perms['table'],
               self.perms['envname'], self.perms['envname'], 
               self.perms['username'], )
        cursor.execute(sql, (self.envname,))
        for username in cursor:
            yield username,'',''  # FIXME: don't we have email addresses in tables now?
        cnx.close()

    def get_known_users(self, cnx=None, limit=None):
        db = get_db(self.env)
        cursor = db.cursor()
        sql = "SELECT %s " \
              "FROM %s " \
              "WHERE (%s=%%s or %s='all') " \
              "ORDER BY %s" % \
              (self.perms['username'], self.perms['table'],
               self.perms['envname'], self.perms['envname'], 
               self.perms['username'], )
        cursor.execute(sql, (self.envname,))
        for username in cursor:
            yield username[0]

    def get_user_attribute(self, user, attr):
        pass
    
    def get_supported_attributes(self):
        pass
