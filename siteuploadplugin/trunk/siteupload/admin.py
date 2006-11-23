# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 John Hampton <pacopablo@asylumware.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at:
# http://trac-hacks.org/wiki/TracBlogPlugin
#
# Author: John Hampton <pacopablo@asylumware.com>

from trac.core import *
from trac.web.chrome import ITemplateProvider
from trac.perm import IPermissionRequestor
from trac.util import Markup, pretty_size
from trac.admin import IAdminPanelProvider

import os
import os.path
import stat
import shutil
from pkg_resources import resource_filename

__all__ = ['SiteuploadAdminPage']

class SiteuploadAdminPage(Component):
    """ Allows for administatrators to upload files to the trac environment's htdocs dir

    Also allows admins to manage files in said dir.

    """

    implements(ITemplateProvider, IAdminPanelProvider, IPermissionRequestor)

    # IPermissionRequestor
    def get_permission_actions(self):
        return ['SITEUPLOAD_MANAGE', 'SITEUPLOAD_UPLOAD', ('SITEUPLOAD_ADMIN', ['SITEUPLOAD_MANAGE', 'SITEUPLOAD_UPLOAD'])]

    # IAdminPanelPageProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('SITEUPLOAD_ADMIN'):
            yield ('siteupload', 'Site Files', 'files', 'Files')

    def render_admin_panel(self, req, cat, page, path_info):
        assert req.perm.has_permission('SITEUPLOAD_ADMIN')
        target_path = os.path.join(self.env.path, 'htdocs')
        readonly = False
        if not (os.path.exists(target_path) and os.path.isdir(target_path) and os.access(target_path, os.F_OK + os.W_OK)):
            readonly = True
        if req.method == 'POST':
            if req.args.has_key('delete'):
                self._do_delete(req)
            elif req.args.has_key('upload'):
                self._do_upload(req)
            else:
                self.log.warning('Unknown POST request: %s', req.args)                                                                               
            req.redirect(self.env.href.admin(cat, page))

        data = {'siteupload' : {'readonly' : readonly}} 
        self._render_view(req, data)
        return 'upload.html', data

    def _render_view(self, req, data):
        """Display list of files in trac env htdocs dir"""
        target_path = os.path.join(self.env.path, 'htdocs')
        filelist = []
        if os.path.exists(target_path) and os.path.isdir(target_path):
            dlist = os.listdir(target_path)
            for f in dlist:
                fsize = os.stat(os.path.join(target_path, f))[stat.ST_SIZE]
                filelist.append({'name' : f,
                                 'link' : Markup('<a href="%s">%s</a>',
                                          self.env.href.chrome('site', f), f), 
                                 'size' : pretty_size(fsize),})
                continue
        data.update({'siteupload' : {'files' : filelist}})
        return

    def _do_delete(self, req):
        """Delete a file from htdocs"""
        target_path = os.path.join(self.env.path, 'htdocs')
        err_list = []
        sel = req.args.get('sel')
        sel = isinstance(sel, list) and sel or [sel]
        for key in sel:
            try:
                os.unlink(os.path.join(target_path, key))
            except OSError:
                err_list.append(key)
            continue
        if err_list:
            errmsg = "Unable to delete the following files:\n"
            errmsg += '\n'.join(err_list)
            raise TracError, errmsg
    
    def _do_upload(self, req):
        """Install a plugin."""
        if not req.args.has_key('site_file'):
            raise TracError, 'No file uploaded'
        upload = req.args['site_file']
        if not upload.filename:
            raise TracError, 'No file uploaded'
        upload_filename = upload.filename.replace('\\', '/').replace(':', '/')
        upload_filename = os.path.basename(upload_filename)
        if not upload_filename:
            raise TracError, 'No file uploaded'

        target_path = os.path.join(self.env.path, 'htdocs', upload_filename)
        if os.path.isfile(target_path):
            raise TracError, 'File name >>%s<< already exists' % upload_filename

        self.log.info('Installing plugin %s', upload_filename)
        flags = os.O_CREAT + os.O_WRONLY + os.O_EXCL
        try:
            flags += os.O_BINARY
        except AttributeError:
            # OS_BINARY not available on every platform
            pass
        target_file = os.fdopen(os.open(target_path, flags), 'w')
        try:
            shutil.copyfileobj(upload.file, target_file)
            self.log.info('File %s uploaded to %s', upload_filename,
                          target_path)
        finally:
            target_file.close()


    # INavigationContributor
    def get_templates_dirs(self):
        """
            Return the absolute path of the directory containing the provided
            templates
        """
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return []

