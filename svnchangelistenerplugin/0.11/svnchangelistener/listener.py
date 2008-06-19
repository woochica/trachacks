#!/usr/bin/env python
"""
SVN Change Listenener pluggable entry point for trac

# This Subversion post-commit hook script is meant to interface to the
# Trac (http://www.edgewall.com/products/trac/) issue tracking/wiki/etc 
# system.
# 
# It should be called from the 'post-commit' script in Subversion, such as
# via:
#
# REPOS="$1"
# REV="$2"
#
# %s -p <project> -r "$REV"
""" % __file__


from svnchangelistener.interface import ISVNChangeListener
from trac.core import *
from trac.env import open_environment
from trac.versioncontrol.api import NoSuchChangeset

class SVNChangeListener(object):
    # XXX this doesn't need to be a class
    def __init__(self, revision, project=None):
        env = open_environment(project)
        repos = env.get_repository()
        repos.sync()
        try:
            chgset = repos.get_changeset(revision)
        except NoSuchChangeset:
            return # out of scope changesets are not cached

        listeners =  ExtensionPoint(ISVNChangeListener).extensions(env)

        for listener in listeners:
            listener.on_change(env, chgset)

if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-p', '--project', '--projects', 
                      dest='projects', action='append', 
                      default=[],
                      help='projects to apply to',
                      )
    parser.add_option('-r', '--revision', help='SVN revision number (required)')

    options, args = parser.parse_args()
    if not options.revision:
        parser.error('SVN revision number required')

    for project in options.projects:
        SVNChangeListener(options.revision, project)
