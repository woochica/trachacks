# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, 2009 Arqiva
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
from pkg_resources import resource_filename
from configobj import ConfigObj
from StringIO import StringIO

from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider

from trac.core import *
from trac.util import translation

from acct_mgr.api import AccountManager


class PageAuthzPolicyEditor(Component):
    implements(IAdminPanelProvider, ITemplateProvider)

    def __init__(self):
        self.account_manager = AccountManager(self.env)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield ('accounts', translation._('Accounts'), 'pages', translation._('Page Permissions'))

    def _get_filename(self, section, name):
      file_name = self.config.get(section, name)
      if (not file_name.startswith(os.path.sep)) and (not file_name[1] == (':')):
	file_name = os.path.join(self.env.path, file_name)
      return(file_name)

    def _get_users(self):
        return(self.account_manager.get_users())
    
    def _group_filename(self):
        group_file_name = self._get_filename('account-manager', 'group_file')
        if not group_file_name:
            group_file_name = self._get_filename('htgroups', 'group_file')
        if not group_file_name:
            raise TracError('Group filename not found in the config file. In neither sections\
                                "account-manager" nor "htgroups" under the name "group_file".')
        if not os.path.exists(group_file_name):
            raise TracError('Group filename not found: %s.' % group_file_name)
        return(group_file_name)

    # Get the groups and their members so they can easily be included in the
    # groups section of the authz file.  Need it as a dictionary of arrays so it be easily
    # iterated.    
    def _get_groups_and_members(self):
        """
        Get the groups and their members as a dictionary of
        lists.
        """
        # could be in one of two places, depending if the 
        # account-manager is installed or not
        group_file_name = self._group_filename()
        groups_dict = dict()
        group_file = file(group_file_name)
        try:
            for group_line in group_file:
                # Ignore blank lines and lines starting with #
                group_line = group_line.strip()
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
        authz_policy_file_name = self._get_filename('authz_policy', 'authz_file')
        group_details = self._get_groups_and_members()
        # Handle the return data
        if req.method == 'POST':
             if req.args.get('authz_file_contents'):
                # The data needs to be validated, otherwise duplicate
                # entries can break things.
                edited_contents = str(req.args.get('authz_file_contents'))
                edited_contents_stringio = StringIO(edited_contents)
                try:
                    test_authz_policy_dict = ConfigObj(edited_contents_stringio)
                except:
                    raise TracError(_('Error in edited file.  Re-edit and check for duplicate entries.'))
                authz_policy_file = open(authz_policy_file_name, 'w')
                test_authz_policy_dict.write(authz_policy_file)
                authz_policy_file.close()

        authz_policy_dict = ConfigObj(authz_policy_file_name)

        # If there isn't a group file, don't destroy the existing entries
        if (group_details):
            authz_policy_dict['groups'] = group_details

        # This is purely to fill in the text area with the contents.
        contents = StringIO()
        authz_policy_dict.write(contents)


        #contents = open(authz_policy_file_name).readlines()
        data = {
            'file_name' : authz_policy_file_name,
            'contents': contents.getvalue(),
            'users' : self._get_users()
        }
        return 'page_authz_policy_editor.html', {'pages_authz': data}

