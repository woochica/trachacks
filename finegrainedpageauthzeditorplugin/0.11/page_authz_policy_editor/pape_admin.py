# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Arqiva
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
# history and logs, available at http://trac.edgewall.org/.
#
# Based on work by Author: Jonas Borgström <jonas@edgewall.com>
# Author: Robert Martin <robert.martin@arqiva.com>

import os
import pkg_resources
from configobj import ConfigObj
#import ConfigParser
from StringIO import StringIO

from genshi import HTML
from genshi.builder import tag

from trac import __version__ as TRAC_VERSION
from trac.admin.api import IAdminPanelProvider
from trac.core import *
from trac.perm import PermissionSystem, IPermissionRequestor
from trac.util.translation import _
from trac.web import HTTPNotFound, IRequestHandler
from trac.web.chrome import add_script, add_stylesheet, add_warning, Chrome, \
                            INavigationContributor, ITemplateProvider


try:
    from webadmin import IAdminPageProvider
except ImportError:
    IAdminPageProvider = None



class PageAuthzPolicyEditor(Component):

    implements(IAdminPanelProvider, ITemplateProvider)


    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        return [pkg_resources.resource_filename('page_authz_policy_editor.pape_admin', 'templates')]


    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield ('accounts', _('Accounts'), 'pages', _('Page Permissions'))

    def _get_groups(self):
        group_file_name = self.config.get('account-manager', 'group_file')
        groups_list = list()
        if os.path.exists(group_file_name):
            group_file = file(group_file_name)
            try:
                for group_line in group_file:
                    group = group_line.strip()
                    # Ignore blank lines and lines starting with #
                    if group_line and not group_line.startswith('#'):
                        group_name = group_line.split(':', 1)[0]
                        groups_list.append('@' + group_name)
            finally:
                group_file.close()
        groups = ', '.join(sorted(groups_list))
        return groups

    def _get_users(self):
        password_file_name = self.config.get('account-manager', 'password_file')
        users_list = list()
        if os.path.exists(password_file_name):
            password_file = file(password_file_name)
            try:
                for user_line in password_file:
                    # Ignore blank lines and lines starting with #
                    if user_line and not user_line.startswith('#'):
                        user_name = user_line.split(':', 1)[0]
                        users_list.append(user_name.strip())
            finally:
                password_file.close()
        users = ', '.join(sorted(users_list))
        return users

    # Get the groups and their members so they can easily be included in the
    # groups section of the authz file.  Need it as a dictionary of arrays so it be easily
    # iterated.
    def _get_groups_and_members(self):
        group_file_name = self.config.get('account-manager', 'group_file')
        if os.path.exists(group_file_name):
            group_file = file(group_file_name)
            try:
                groups_dict = dict()
                for group_line in group_file:
                    group = group_line.strip()
                    # Ignore blank lines and lines starting with #
                    if group_line and not group_line.startswith('#'):
                        group_name = group_line.split(':', 1)[0]
                        group_members = group_line.split(':', 2)[1].split(' ')
                        groups_dict[group_name] = [ x for x in [member.strip() for member in group_members] if x ]
            finally:
                group_file.close()
        if len(groups_dict):
            return groups_dict
        else:
            return None

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('TRAC_ADMIN')
        authz_policy_file_name = self.config.get('authz_policy', 'authz_file')
        group_details = self._get_groups_and_members()
        # Handle the return data
        if req.method == 'POST':
             if req.args.get('authz_file_contents'):
                edited_contents = req.args.get('authz_file_contents')
                authz_policy_file = open(authz_policy_file_name, 'w')
                authz_policy_file.write(edited_contents)
                authz_policy_file.close()

        authz_policy_file = ConfigObj(authz_policy_file_name)

        # If there isn't a group file, don't destroy the existing entries
        if (group_details):
            authz_policy_file['groups'] = group_details

        # This is purely to fill in the text area with the contents.
        contents = StringIO()
        authz_policy_file.write(contents)


        #contents = open(authz_policy_file_name).readlines()
        data = {
            'file_name' : authz_policy_file_name,
            'contents': contents.getvalue(),
            'users' : self._get_users(),
            'groups' : self._get_groups()
        }
        return 'page_authz_policy_editor.html', {'pages_authz': data}

