# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Radu Gasler <miezuit@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import sys
import os
import time
import optparse

from trac.core import *
from trac.env import Environment

from wikireplace.util import wiki_text_replace

def username():
    """Find the current username."""
    if os.name == 'nt': # Funny windows hack
        return os.environ['USERNAME']
    else:
        return os.getenv('USER')

def main(*argv):
    parser = optparse.OptionParser(usage='Usage: %prog old-text new-text wiki-page ... trac-env', version='ReplaceInPage 1.0')
    parser.add_option('-d','--debug',help='Activate debugging', action='store_true', default=False)
    (options, args) = parser.parse_args(list(argv[1:]))
    if len(args) < 3:
        parser.error("Not enough arguments")

    oldname = args[0]
    newname = args[1]
    wikipages = args[2:len(args)-2]
    envpath = args[len(args-1)]
    env = Environment(envpath)
    wiki_text_replace(env, oldtext, newtext, wikipages, username(), '127.0.0.1', debug=options.debug)

def run():
    main(*sys.argv)
    
if __name__ == '__main__':
    run()
