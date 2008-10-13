"""
trac plugin that front-ends the creation and syncing of a 
remote svn repository

you MUST have svn and svnsync installed to use this plugin
"""

import subprocess
import svnsync

from trac.config import Option
from trac.core import *
from trac.versioncontrol import IRepositoryConnector
from trac.versioncontrol.svn_fs import SubversionConnector
from trac.versioncontrol.svn_fs import SubversionRepository

class SvnsyncConnector(SubversionConnector):
    implements(IRepositoryConnector)

    repository_url = Option('svn', 'repository_url', '',
                            """url of the remote repository""")

    # methods for IRepositoryConnector

    def get_supported_types(self):
        """support for `repository_type = svnsync`"""
        if self.has_svnsync():
            yield('svnsync', 8)

    def get_repository(self, repos_type, repos_dir, authname):
        assert repos_type == 'svnsync'

        # sync the repository
        directory = self.env.config.get('trac', 'repository_dir')
        svnsync.sync(directory, self.repository_url, logger=self.env.log.info)

        repos = SubversionRepository(repos_dir, None, self.log)
        return repos
        
    ### methods particular to SvnsyncConnector

    def has_svnsync(self):
        """
        ensures that the environment is sane for svnsync to work
        """        

        if not self.repository_url:
            return False

        # these commands need to work for the plugin to work
        required_commands = ( ( 'svnsync', 'help' ),
                              ( 'svnadmin', 'help' ),
                              ( 'svn', 'help'), )
        
        for command in required_commands:
            try:
                process = subprocess.Popen(command, 
                                           stdout=subprocess.PIPE, 
                                           stderr=subprocess.PIPE)

                if process.wait() != 0:
                    return False

            except OSError:
                # usually this means the command is not installed
                # TODO:  log the exception
                return False

        return True
