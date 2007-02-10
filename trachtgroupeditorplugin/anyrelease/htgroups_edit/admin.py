# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Chris Liechti <cliechti@gmx.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. It is the
# new BSD license.

from trac.core import *
from trac.util import sorted
from webadmin.web_ui import IAdminPageProvider
from trac.web.chrome import ITemplateProvider
import os

class HtGroupEditorAdminPage(Component):

    implements(IAdminPageProvider, ITemplateProvider)

    # IAdminPageProvider
    
    def get_admin_pages(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('accounts', 'Accounts', 'groups', 'Groups')

    def process_admin_request(self, req, cat, page, path_info):
        if cat == 'accounts' and page == 'groups': 
            return self._do_htgroup(req)

    def _do_htgroup(self, req):
        """Provide a list of groups, a current group name and a list
        of users in the current group.
        """
        # get the groups from the database file
        groups = self.get_groups()
        
        # prepare the selection and user list
        group_name = req.args.get('group')
        if not group_name or group_name not in groups:
            # no group name given, try to use a default
            if groups: #not empty
                group_name = sorted(groups.keys())[0]
            else:
                group_name = None
        
        
        # process forms/commands
        if req.method == 'POST':
            if req.args.get('add'):
                new_group = req.args.get('new_group')
                new_user = req.args.get('new_user')
                groups.setdefault(new_group, []).append(new_user)
                self.write_groups(groups)
                req.hdf['message'] = u'added %s to %s' % (new_user, new_group)
            elif req.args.get('remove') and req.args.get('group'):
                sel = req.args.get('sel')
                sel = isinstance(sel, list) and sel or [sel]
                for user in sel:
                    groups[req.args.get('group')].remove(user)
                self.write_groups(groups)
                req.hdf['message'] = u'removed %s from %s' % (sel, req.args.get('group'))
        # listst and other info
        req.hdf['groups'] = sorted(groups.keys())
        listing_enabled = isinstance(group_name, basestring) and group_name in groups
        if listing_enabled:
            req.hdf['group'] = group_name
            req.hdf['members'] = sorted(groups[group_name])

        req.hdf['listing_enabled'] = listing_enabled
        req.hdf['selection_enabled'] = len(groups.keys()) > 1
        return 'htgroup_editor.cs', None

    # ITemplateProvider
    
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return []

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # --- helpers
    
    def get_group_filename(self):
        # get file name from configuration
        if 'htgroup-editor' in self.config:
            group_file_name = self.config.get('htgroup-editor', 'group_file')
        elif 'account-manager' in self.config:
            group_file_name = self.config.get('account-manager', 'group_file')
        else:
            self.env.log.error('no htgroup-editor or account-manager config for group_file found')
        return group_file_name
    
    def get_groups(self):
        """parse group file"""
        groups = {}
        group_file_name = self.get_group_filename()
        
        #load the file into the memory
        if os.path.exists(group_file_name):
            group_file = file(group_file_name)

            try:
                for group in group_file:
                    group = group.strip()
                    if group and not group.startswith('#'):
                        group_name, group_members = group.split(':', 1)
                        groups[group_name] = group_members.split()
            finally:
                group_file.close()

        self.env.log.debug('htgroup-editor read %r' % (group_file_name,))

        # give a dictionary with group->user list mapping
        return groups

    def write_groups(self, groups):
        """write new group file"""
        group_file_name = self.get_group_filename()
        
        #load the file into the memory
        if os.path.exists(group_file_name):
            group_file = file(group_file_name, 'w')
            try:
                for group_name in sorted(groups):
                    if groups[group_name]: #if non empty
                        group_file.write('%s: %s\n' % (
                            group_name,
                            ' '.join(sorted(groups[group_name]))
                        ))
            finally:
                group_file.close()

        self.env.log.debug('htgroup-editor wrote %r' % (group_file_name,))

