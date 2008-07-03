#!/usr/bin/env python

"""
script to create a trac plugin given the interfaces to be used
"""

import os
import subprocess
import sys

from create_trac_plugin.create_component import check_interfaces
from create_trac_plugin.create_component import parse_args
from create_trac_plugin.create_component import print_component

def main():

    ### parse the arguments
    parse_args()

    ### check to ensure that the interfaces given actually exist
    nonexistant = check_interfaces(*sys.argv[2:])
    if nonexistant:
        print "Error: interfaces specified not found: " + ', '.join(nonexistant)
        sys.exit(1)

    ### run paster create -t trac_plugin
    ### this should be installed as a dependency
    # XXX this should probably use python code instead of shelling out
    subprocess.call(['paster', 'create', '-t', 'trac_plugin', sys.argv[1]])

    # figure out what paster did
    project = sys.argv[1].lower()
    filename = os.path.join(sys.argv[1], project, '%s.py' % project)

    ### (re)generate the plugin file based on the interfaces passed
    component = print_component(*sys.argv[1:])
    module = file(filename, 'w')
    print >> module, component
    module.close()
                
if __name__ == '__main__':
    main()
                         
