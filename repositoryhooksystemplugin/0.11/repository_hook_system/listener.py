#!/usr/bin/env python
"""
Repository Change Listener plugin for trac

This module provides an entry point for trac callable 
from the command line
"""

import os
import sys

from optparse import OptionParser
from repository_hook_system.interface import IRepositoryChangeListener
from trac.core import *
from trac.env import open_environment
from trac.versioncontrol.api import NoSuchChangeset

class RepositoryChangeListener(object):
    # XXX this doesn't need to be a class...yet!    

    def __init__(self, project, hook, *args):
        """
        * project : path to the trac project environment
        * hook : name of the hook called from
        * args : arguments for the particular implementation of IRepositoryChangeListener
        """

        # open the trac environment 
        env = open_environment(project)
        repo = env.get_repository() # XXX multiproject branch
        repo.sync()

        # find the active listeners
        listeners = ExtensionPoint(IRepositoryChangeListener).extensions(env)
        
        # find the listener for the given repository type and invoke the hook
        for listener in listeners:
            if env.config.get('trac', 'repository_type') in listener.type():
                changeset = listener.changeset(repo, *args)
                subscribers = listener.subscribers(hook)
                for subscriber in subscribers:
                    subscriber.invoke(changeset)
        
def filename():
    return os.path.abspath(__file__.rstrip('c'))

def command_line(projects, hook, *args):
    """return a generic command line for invoking this file"""

    # arguments to the command line
    # XXX this could be returned as a list, if there is a reason to do so
    retval = [ sys.executable, filename() ]
    
    # enable passing just one argument
    if isinstance(projects, basestring):
        projects = [ projects ]

    # append the projects to the command line
    for project in projects:
        retval.extend(['-p', project])
        
    # add the hook
    retval.extend(['--hook', hook])

    # add the arguments
    retval.extend(args)

    return ' '.join(retval)

def option_parser():
    parser = OptionParser()
    parser.add_option('-p', '--project', '--projects', 
                      dest='projects', action='append', 
                      default=[],
                      help='projects to apply to',
                      )
    parser.add_option('--hook',
                      dest='hook',
                      help='hook called')
    return parser

if __name__ == '__main__':

    # obtain command line options
    # the arguments should be those needed for the particular
    # implementation of IRepositoryChangeListener
    parser = option_parser()
    options, args = parser.parse_args()

    # TODO: ensure --hook is passed

    for project in options.projects:
        RepositoryChangeListener(project, options.hook, *args)
