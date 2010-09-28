#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
$Id$
"""

from pkg_resources import resource_filename
from trac.core import *
from trac.admin.api import IAdminPanelProvider, IAdminCommandProvider
from trac.web.chrome import ITemplateProvider


class IUserRenamer(Interface):

    def rename_user(oldname, newname, db=None):
        """Renames user 'oldname' to 'newname'.
           Can return a message or a list of messages to be shown to
           the user."""
        pass
