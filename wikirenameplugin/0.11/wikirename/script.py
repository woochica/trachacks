#!/usr/bin/env python
import sys
import os
import time
import optparse

from trac.core import *
from trac.env import Environment

from wikirename.util import rename_page

def username():
    """Find the current username."""
    if os.name == 'nt': # Funny windows hack
        return os.environ['USERNAME']
    else:
        return os.getlogin()

def main(*argv):
    parser = optparse.OptionParser(usage='Usage: %prog old-name new-name trac-env', version='RenamePage 2.0')
    parser.add_option('-d','--debug',help='Activate debugging', action='store_true', default=False)
    (options, args) = parser.parse_args(list(argv[1:]))
    if len(args) < 3:
        parser.error("Not enough arguments")

    oldname = args[0]
    newname = args[1]
    envpath = args[2]
    env = Environment(envpath)
    rename_page(env, oldname, newname, username(), '127.0.0.1', debug=options.debug)

def run():
    main(*sys.argv)
    
if __name__ == '__main__':
    run()
