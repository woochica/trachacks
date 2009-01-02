"""
implementation of the RepositoryChangeListener interface for svn
"""

import os
import subprocess

from genshi.builder import tag
from repository_hook_system.filesystemhooks import FileSystemHooks
from repository_hook_system.interface import IRepositoryChangeListener
from repository_hook_system.interface import IRepositoryHookSubscriber
from repository_hook_system.interface import IRepositoryHookSystem
from trac.config import Option
from trac.config import ListOption
from trac.core import *
from trac.util.text import CRLF
from utils import iswritable

class SVNHookSystem(FileSystemHooks):
    """implementation of IRepositoryChangeListener for SVN repositories"""

    implements(IRepositoryHookSystem, IRepositoryChangeListener)
    listeners = ExtensionPoint(IRepositoryHookSubscriber)
    hooks = [ 'pre-commit', 'post-commit', 'pre-revprop-change', 'post-revprop-change' ]


    _svnlook = Option('svn', 'svnlook', default='/usr/bin/svnlook')

    ### methods for FileSystemHooks

    def filename(self, hookname):
        location = self.env.config.get('trac', 'repository_dir')
        return os.path.join(location, 'hooks', hookname)

    def args(self):
        return [ '$2' ]

    ### methods for IRepositoryHookAdminContributer

    def render(self, hookname, req):
        filename = self.filename(hookname)
        try:
            contents = file(filename).read() # check for CRLF here too?
            return tag.textarea(contents, rows='25', cols='80', name='hook-file-contents', disabled=not self.can_enable(hookname) or None)

        except IOError:
            if self.can_enable(filename):
                text = "No %s hook file yet exists;  enable this hook to create one" % hookname
            else:
                text = "The file, %s, is unwritable;  enabling this hook will have no effect" % filename
            return text

    def process_post(self, hookname, req):
        
        contents = req.args.get('hook-file-contents', None)
        if contents is None:
            return
        if os.linesep != CRLF:
            contents = os.linesep.join(contents.split(CRLF)) # form contents will have this

        filename = self.filename(hookname)
        if not os.path.exists(filename):
            if not iswritable(filename):
                return # XXX error handling?
            os.mknod(self.mode)
        f = file(filename, 'w')
        print >> f, contents

    ### methods for IRepositoryChangeListener

    def type(self):
        return ['svn', 'svnsync']

    def available_hooks(self):
        return self.hooks

    def subscribers(self, hookname):
        """returns the active subscribers for a given hook name"""
        
        # XXX this is all SCM-agnostic;  should be moved out
        return [ subscriber for subscriber in self.listeners 
                 if subscriber.__class__.__name__ 
                 in getattr(self, hookname, []) 
                 and subscriber.is_available(self.type(), hookname) ]

    def changeset(self, repo, hookname, commit_id):
        """ 
        return the changeset given the repository object and revision number
        """

        if hookname in ['post-commit', 'post-revprop-change']:
            revision = commit_id
            try:
                
                chgset = repo.get_changeset(revision)
            except NoSuchChangeset:
                # XXX should probably throw an exception (same one?)
                return # out of scope changesets are not cached
            return chgset
        else:
            transaction = commit_id
            repo = self.env.config.get('trac', 'repository_dir')

            def svnlook(subcommand, *args):

                process = subprocess.Popen([self._svnlook, subcommand, repo, '-r', transaction] + list(args), stdout=subprocess.PIPE)
                return process.communicate()[0]

            # get the attributes
            author = svnlook('author').strip()
            from dateutil.parser import parse
#            import pdb;  pdb.set_trace()
            date = parse(svnlook('date').split('(')[0].strip())

            
            message = svnlook('log').strip()
            rev = transaction

            # XXX FIXME
#             from datetime import datetime
#             date = datetime.now()

            attributes = dict(author=author,
                              date=date,
                              message=message,
                              rev=rev)
            chgset = type('DummyChangeset', (object,), attributes)
            return chgset()
            

for hook in SVNHookSystem.hooks:
    setattr(SVNHookSystem, hook, 
            ListOption('repository-hooks', hook, default=[],
                       doc="active listeners for SVN changes on the %s hook" % hook))
