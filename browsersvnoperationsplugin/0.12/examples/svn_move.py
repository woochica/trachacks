#!/usr/bin/env python
'''
Usage: %s [-m commitmsg] [-u username] repos-url repos-url

Move a file or directory within a Subversion repository
'''

import getopt
import os
import sys

from svn import core, fs, repos, client

def svn_move(src_path, dst_path, username='', commitmsg=''):
    '''Move src_path to dst_path, where each is the url to a file or directory
    in a Subversion repository. Apply the change as username, and log with 
    commitmsg.
    '''
    
    def log_message(items, pool):
        '''Return a commit log message, use as a callback
        '''
        def fname(s): return s.rstrip('/').rsplit('/', 1)[1]
        src_fname = fname(items[1][2])
        dst_fname = fname(items[0][2])
        default_msg = 'Moved %s to %s' % (src_fname, dst_fname)
        return commitmsg or default_msg
    
    src_path = core.svn_path_canonicalize(src_path)
    dst_path = core.svn_path_canonicalize(dst_path)
    
    force = False # Ignored for repository -> repository moves
    move_as_child = False # If dst_path exists don't attempt to move src_path  
                          # as it's child
    make_parents = False # Make parents of dst_path as needed (like mkdir -p)
    revprop_tbl = None # Use a dict of str prop: vals to set custom svn props 
    
    # The move operation is coordinated by a client context, suitbly populated
    # To set the commit message we provide a callback that returns commitmsg
    client_ctx = client.create_context()
    client_ctx.log_msg_func3 = client.svn_swig_py_get_commit_log_func
    client_ctx.log_msg_baton3 = log_message
    
    # Configure minimal authentication, this is an example only
    auth_providers = [client.svn_client_get_simple_provider(),
                      client.svn_client_get_username_provider(),
                      ]
    client_ctx.auth_baton = core.svn_auth_open(auth_providers)
    
    # libsvn normally infers the username from the environment the working copy
    # and the configuration. If requested override all that.
    if username is not None:
        core.svn_auth_set_parameter(client_ctx.auth_baton, 
                core.SVN_AUTH_PARAM_DEFAULT_USERNAME, username)
    
    # Move one directory or file to another location in the same repository
    # svn_client_move5 can mv a number of files/directories at once if dst_path
    # is a directory, we ignore this and pass a 1-tuple
    commit_info = client.svn_client_move5((src_path,),
                                          dst_path,
                                          force, # Ignored
                                          move_as_child,
                                          make_parents,
                                          revprop_tbl,
                                          client_ctx,
                                          )
    print commit_info.revision

def usage(prog_name):
    print (__doc__ % prog_name).strip('\n')
    
def main():
    prog_name = sys.argv[0]
    opts, args = getopt.getopt(sys.argv[1:], 'm:u:')
    if len(args) != 2:
        usage(prog_name)
        sys.exit(1)

    username = commitmsg = None

    for name, value in opts:
        if name == '-u':
            username = value
        if name == '-m':
            commitmsg = value
    
    svn_move(args[0], args[1], username, commitmsg)

if __name__ == '__main__':
    main()
