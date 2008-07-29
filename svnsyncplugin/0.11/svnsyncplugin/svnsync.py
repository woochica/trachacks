#!/usr/bin/env python

"""
process to create and sync a remote subversion repository using svnsync
see http://svn.collab.net/repos/svn/trunk/notes/svnsync.txt
this is done in python instead of bash for portability
"""

import os
import subprocess

windows = [ 'nt' ] # special-casing for windows OS;  POSIX assumed otherwise

def sh(*args, **kw):
    """execute command line arguments.  return stdout, stderr, returncode"""
    command = ' '.join(args)
    verbose = kw.get('verbose', True)
    if verbose:
        print '> %s' % command
    try:
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError, e:
        return ('', '%s: %s' % (command, e.strerror), 127)
    stdout, stderr = process.communicate()
    return (stdout, stderr, process.wait())

def file_uri(path):
    # this should really live elsewhere
    if os.name in windows: 
        uri = 'file:///' + os.path.abspath(path) 
        uri = uri.replace('\\','/') 
    else: 
        uri = 'file://' + os.path.abspath(path) 
    return uri

def create(directory, repository, username='svnsync'):
    """create a mirror of remote repository at directory"""

    ### create the repository

    sh('svnadmin', 'create', directory)

    filename = 'pre-revprop-change'
    if os in windows:
        filename += '.bat'
    filename = os.path.join(directory, 'hooks', filename)
    os.mknod(filename, 0770)
    f = file(filename, 'w')
    if os in windows:
        print >> f, ''
    else:
        print >> f, '#!/bin/sh'
        f.close()

    ### initialize the sync

    return sh('svnsync', 'init', '--username', username, 
              file_uri(directory), repository)

def sync(directory, repository, username='svnsync'):

    # create the mirror if it doesn't exist
    if not os.path.exists(directory):
        retval = create(directory, repository, username)
        if retval[-1] != 0:
            return retval

    repo = file_uri(directory)

    # ensure that the repository is pointed at the right place
    propget = sh('svn', 'propget',  'svn:sync-from-url', '--revprop', '-r', '0', repo)
    
    url = propget[0].strip()
    if url != repository.rstrip('/'):
        print '>>> repository changed! %s -> %s' % (url, repository.strip())
        print '> resyncing to new repository'
        import shutil
        shutil.rmtree(directory)
        sync(directory, repository, username)

    return sh('svnsync', 'sync', repo)

if __name__ == '__main__':
    import optparse
    import sys

    # parse command line options
    parser = optparse.OptionParser()
    parser.add_option('--directory')
    parser.add_option('--repository')
    parser.add_option('--username', default='svnsync')

    options, args = parser.parse_args()

    for option in 'directory', 'repository':
        if not getattr(options, option):
            print '%s not specified' % option
            parser.print_help()
            sys.exit(1)

    # sync the repository, setting up if necessary
    result = sync(options.directory, options.repository, options.username)

    if result[2] != 0:
        print '--ERROR--'
        print '-> stdout:\n%s' % result[0]
        print '-> stderr:\n%s' % result[1]
