"""
installer for the post-commit-hook for SVNChangeListener
"""

import os
import pkg_resources
import svnchangelistener.listener
import sys
import tempfile

from trac.admin.api import IAdminPanelProvider
from trac.core import *
from trac.web.chrome import ITemplateProvider

### methods

def iswritable(filename):
    if os.path.exists(filename):
        return os.access(filename, os.W_OK)
    else:
        
        # XXX try to make the file and delete it,
        # as this is easier than figuring out permissions
        try:
            file(filename, 'w').close()
        except IOError:
            return False

        os.remove(filename) # remove the file stub
        return True

def commandline(*projects):

    # if you don't have any projects, you shouldn't be here
    assert len(projects) 
    
    rev = '"$2"'

    # use the .py file, not the .pyc file
    listener = svnchangelistener.listener.__file__.rstrip('c')

    return '%s %s %s -r %s' % (sys.executable,
                               listener, 
                               ' '.join(['-p %s' % project
                                         for project in projects]),
                               rev)

def post_commit_file(repository):
    return os.path.join(repository, 'hooks', 'post-commit')

def post_commit_hook(*projects):
    """contents of a new post-commit-hook file"""

    return """#!/bin/bash
%s
""" % commandline(*projects)

def create_post_commit_hook(repository, *projects):
    """
    create a new post-commit-hook file 
    * repository:  path to the repository
    * projects:  list of projects to append listen for changes on
    """

    filename = post_commit_file(repository)
    try:
        post_commit  = file(filename, 'w')
    except IOError:
        # TODO: probably err more elegantly
        raise
    
    print >> post_commit, post_commit_hook(*projects)
    post_commit.close()
    os.chmod(filename, 0775) # XXX security?

def append_post_commit_hook(repository, *projects):
    filename = post_commit_file(repository)
    try:
        post_commit  = file(filename, 'a')
    except IOError:
        # TODO: probably err more elegantly
        raise
    print >> post_commit, commandline(*projects)
    post_commit.close()
    
class SVNChangeListenerInstaller(Component):
    

    implements(IAdminPanelProvider, ITemplateProvider)

    ### methods for IAdminPanelProvider

    def get_admin_panels(self, req):
        """Return a list of available admin panels.
        
        The items returned by this function must be tuples of the form
        `(category, category_label, page, page_label)`.
        """
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('svn', 'SVN', 'changelistener', 'Change Listener')

    def render_admin_panel(self, req, category, page, path_info):
        """Process a request for an admin panel.
        
        This function should return a tuple of the form `(template, data)`,
        where `template` is the name of the template to use and `data` is the
        data to be passed to the template.
        """
        data = {} # data for template

        filename = post_commit_file(self.env.config.get('trac', 'repository_dir'))
        data['filename'] = filename
        data['commandline'] = commandline(self.env.path)

        if req.method == 'POST':

            # assume unix format
            contents = req.args['contents'].replace('\r', '')

            exists = os.path.exists(filename)

            # write the file
            post_commit = file(filename, 'w')
            print >> post_commit, contents
            post_commit.close()

            # default permissions if new file
            os.chmod(filename, 0755)

            return ('success-post-commit-hook.html', data)

        if not iswritable(filename):
            return ('unwritable-post-commit-hook.html', data)

        if os.path.exists(filename):
            data['file_contents'] = file(filename).read()
            data['file_contents'] += '\n# call SVN Change Listener\n' + data['commandline']
            return ('append-post-commit-hook.html', data)
        else:
            data['file_contents'] = post_commit_hook(self.env.path) 
            return ('create-post-commit-hook.html', data)

    ### methods for ITemplateProvider

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return []

    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        
        return [pkg_resources.resource_filename(__name__, 'templates')]

if __name__ == '__main__':
    # TODO: command line install
    pass
