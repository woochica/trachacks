#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
$Id$
"""

from pkg_resources import resource_filename
from trac.core import *
from trac.admin.api import IAdminPanelProvider, IAdminCommandProvider
from trac.web.chrome import ITemplateProvider
from tracrenameuser.api import IUserRenamer


class TestRenamer(Component):
    implements(IUserRenamer)

    def rename_user(self, oldname, newname):
        self.log.debug("blablabla")
        return "Test %s -> %s" % (oldname,newname)


class UserRenameManager(Component):
    """Manages the user renaming process by providing a admin panel and command,
       The actual renaming is done by the implementations of the IUserRenamer
       interface."""
    implements(ITemplateProvider, IAdminPanelProvider, IAdminCommandProvider)
    renamers = ExtensionPoint(IUserRenamer)

    ## Methods for ITemplateProvider ########################################
    def get_htdocs_dirs(self):
        return []
        #return [('renameuser', resource_filename(__name__, 'htdocs'))]


    def get_templates_dirs(self):
        return [ resource_filename(__name__, 'templates') ]


    ## Methods for IAdminPanelProvider ######################################
    def get_admin_panels(self, req):
        """Return a list of available admin panels.
        
        The items returned by this function must be tuples of the form
        `(category, category_label, page, page_label)`.
        """
        return [("accounts", "Accounts", "renameuser", "Rename User")]

    def render_admin_panel(self, req, category, page, path_info):
        """Process a request for an admin panel.
        
        This function should return a tuple of the form `(template, data)`,
        where `template` is the name of the template to use and `data` is the
        data to be passed to the template.
        """
        data = {'messages':[]}
        if req.method == 'POST':
            if 'oldname' in req.args and 'newname' in req.args:
                messages = self.rename_user(req.args['oldname'], req.args['newname'])
                if messages:
                    data['messages'] = messages
        return ("renameuser.html", data)


    ## Methods for IAdminCommandProvider ####################################
    def get_admin_commands(self):
        return [("renameuser", "oldname newname", "Renames user name", self._complete, self._execute)]

    def _complete(self):
        return ''

    def _execute(self, oldname, newname):
        messages = self.rename_user(oldname, newname)
        for message in messages:
            print message


    def rename_user(self, oldname, newname):
        self.log.info("Renaming '%s' to '%s'" % (oldname,newname))
        messages = [] 
        for renamer in self.renamers:
            msg = renamer.rename_user(oldname, newname)
            if msg:
                if hasattr(msg,'__iter__'):
                    messages.extend(list(msg))
                else:
                    messages.append(msg)
        return messages

# EOF
