# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Edgewall Software
# Copyright (C) 2005 Jonas Borgström <jonas@edgewall.com>
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
# Author: Jonas Borgström <jonas@edgewall.com>

import re

from trac.core import *
from trac.perm import PermissionSystem
from webadmin.web_ui import IAdminPageProvider

from config import EnvironmentOption

class PermissionAdminPage(Component):

    implements(IAdminPageProvider)

    # IAdminPageProvider
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRACFORGE_ADMIN'):
            yield ('tracforge', 'TracForge', 'perm', 'Permissions')

    def process_admin_request(self, req, cat, page, path_info):
        perm = PermissionSystem(self.env)        
        perms = self._get_all_permissions()
        subject = req.args.get('subject')
        action = req.args.get('action')
        group = req.args.get('group')

        if req.method == 'POST':
            # Grant permission to subject
            if req.args.get('add') and subject and action:
                if action not in perm.get_actions():
                    raise TracError('Unknown action')
                self._grant_permission(subject, action)
                req.redirect(self.env.href.admin(cat, page))

            # Add subject to group
            elif req.args.get('add') and subject and group:
                self._grant_permission(subject, group)
                req.redirect(self.env.href.admin(cat, page))

            # Remove permissions action
            elif req.args.get('remove') and req.args.get('sel'):
                sel = req.args.get('sel')
                sel = isinstance(sel, list) and sel or [sel]
                for key in sel:
                    subject, action = key.split(':', 1)
                    if (subject, action) in perms:
                        self._revoke_permission(subject, action)
                req.redirect(self.env.href.admin(cat, page))
        
        perms.sort(lambda a, b: cmp(a[0], b[0]))
        req.hdf['admin.actions'] = perm.get_actions()
        req.hdf['admin.perms'] = [{'subject': p[0],
                                   'action': p[1],
                                   'key': '%s:%s' % p
                                  } for p in perms]
        
        return 'admin_perm.cs', None

    # Internal methods
    def _get_all_permissions(self):
        """Get all permissions from the central table."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT username,action FROM tracforge_permission")
        return [(row[0], row[1]) for row in cursor]

    def _grant_permission(self, username, action):
        """Grants a user the permission to perform the specified action for the central table."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("INSERT INTO tracforge_permission VALUES (%s, %s)",
                       (username, action))
        self.log.info('Granted central permission for %s to %s' % (action, username))
        db.commit()
        
    def _revoke_permission(self, username, action):
        """Revokes a users' permission to perform the specified action from the central table."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("DELETE FROM tracforge_permission WHERE username=%s AND action=%s",
                       (username, action))
        self.log.info('Revoked central permission for %s to %s' % (action, username))
        db.commit()
