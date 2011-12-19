# SVNAdmin plugin

import os
import os.path
import time
import subprocess
import shutil

from trac.admin import AdminCommandError
from trac.config import ListOption, Option
from trac.core import *
from trac.resource import IResourceManager, Resource, ResourceNotFound
from trac.util.concurrency import threading
from trac.util.text import printout, to_unicode
from trac.util.translation import _
from trac.web.api import IRequestFilter
from trac.versioncontrol import IRepositoryProvider, RepositoryManager

class SvnRepositoryProvider(Component):
    """Component providing repositories registered in the SVN parent directory."""

    implements(IRepositoryProvider)
    
    def __init__(self):
        self.parentpath = self.config.get('svnadmin', 'parent_path')
        self.client = self.config.get('svnadmin', 'svn_client_location')
        self.admin = self.config.get('svnadmin', 'svnadmin_location')
    
    def get_repositories(self):
        """Retrieve repositories in the SVN parent directory."""
        if not self.parentpath or not os.path.exists(self.parentpath):
            return []
        repos = os.listdir(self.parentpath)
        reponames = {}
        for name in repos:
            dir = os.path.join(self.parentpath, name)
            
            command = self.admin + ' verify "%s"' % dir
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            (result, error) = process.communicate()
            
            rev = result[result.rfind('revision') + 9:len(result) - 2]
            displayrev = rev
            if rev == '0':
                rev = ''
                displayrev = ''
            reponames[name] = {
                'dir': dir,
                'rev': rev,
                'display_rev': displayrev
            }
        return reponames.iteritems()
    
    def add_repository(self, name):
        """Add a repository."""
        dir = os.path.join(self.parentpath, name)
        if not os.path.isabs(dir):
            raise TracError(_("The repository directory must be absolute"))
        trunk = os.path.join(dir, 'trunk')
        branches = os.path.join(dir, 'branches')
        tags = os.path.join(dir, 'tags')
        command = '"%(svnadmin)s" create "%(dir)s"; "%(svn)s" mkdir --parents -q -m "Created Folders" "file://%(trunk)s" "file://%(branches)s" "file://%(tags)s"' % {
            'svnadmin': self.admin,
            'dir': dir,
            'svn': self.client,
            'trunk': trunk,
            'branches': branches,
            'tags': tags
        }
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (result, error) = process.communicate()
        if error is not None and error != "":
            if error.find('E165002') > -1:
                raise TracError(_('The repository "%(name)s" already exists.', name=name))
            elif error.find('E000002') > -1 or error.find('E000013') > -1:
                raise TracError(_("Can't create the repository '%(name)s.' "
                                  "Make sure the parent directory '%(parentpath)s' exists "
                                  "and the web server has write permissions for it.", name=name, parentpath=self.parentpath))
            else:
                raise TracError(error)
        rm = RepositoryManager(self.env)
        rm.reload_repositories()
    
    def remove_repository(self, name):
        """Remove a repository."""
        try:
            dir = os.path.join(self.parentpath, name)
            shutil.rmtree(dir)
            rm = RepositoryManager(self.env)
            rm.reload_repositories()
        except OSError, why:
            raise TracError(str(why))