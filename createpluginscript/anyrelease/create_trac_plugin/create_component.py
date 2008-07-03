#!/usr/bin/env python
"""
script to create a trac component skeleton file
"""

# TODO:  genericize this
# much of this has nothing to do with trac and could be abstracted
# to its own package

# TODO: ifaces should be a global;  it doesn't change per run

import inspect
import sys
from cStringIO import StringIO
from trac.core import *

# interfaces live in these modules
import trac.admin
import trac.attachment
import trac.db
import trac.env
import trac.mimeview
import trac.perm
import trac.prefs
import trac.resource
import trac.search
import trac.ticket
import trac.timeline
import trac.versioncontrol
import trac.versioncontrol.web_ui
import trac.web
import trac.web.chrome
import trac.wiki

def trac_interfaces():
    """return a dictionary of the trac interfaces: 
    { class.__name__: class }
    """

    retval = {}
    for interface in Interface.__subclasses__():
        retval[interface.__name__] = interface
    return retval

def check_interfaces(*interfaces):
    ifaces = trac_interfaces()
    if not set(interfaces).issubset(ifaces.keys()):
        # XXX redundant?
        return set(interfaces).difference(ifaces.keys())


def print_interface(interface):    
    """return a string of the methods given an interface"""
    # XXX maybe this should use StringIO too?

    # add a section marker
    retval = [ '    ### methods for %s\n' % interface.__name__ ]

    # add the docstring if it exists (useful?)
    doc = interface.__doc__
    if doc:
        retval.append('    """%s"""\n' % doc)

    # add the methods
    args = lambda x: inspect.formatargspec(*inspect.getargspec(x))
    for method_name in [ i for i in dir(interface) if not i.startswith('_') ]:
        method = getattr(interface, method_name)
        if not hasattr(method, '__call__'):
            continue
        argstring = args(method)[1:-1]
        if argstring:
            retval.append('    def %s(self, %s):' % (method_name, argstring))
        else:
            retval.append('    def %s(self):' % method_name)
        doc = method.__doc__
        if doc:
            retval.append('        """%s"""\n' % doc)

    # return the string
    return '\n'.join(retval)

def print_component(name, *interfaces):
    """
    prints the skeleton for a new component 
    given its name and the interfaces it uses
    """
    
    # get the interfaces
    ifaces = trac_interfaces()
    keys = sorted(ifaces.keys())
    
    # check to ensure that the interfaces given actually exist
    # if not, exit with an error
    nonexistant = check_interfaces(*interfaces)
    if nonexistant:
        print "Error: interfaces specified not found: " + ', '.join(nonexistant)
        sys.exit(1)

    # print the docstring and core import
    retval = StringIO()
    print >> retval, '''"""
%s:
a plugin for Trac
http://trac.edgewall.org
"""

from trac.core import *
''' % name

    # print the imports necessary for the interfaces
    for i in interfaces:
        print >> retval, 'from %s import %s' % (ifaces[i].__module__, i)

    # print class declaration
    print >> retval, '\nclass %s(Component):\n'  % name
    print >> retval, '    implements(%s)\n' % ', '.join(interfaces)

    # print the methods needed by the class for its interfaces
    for i in interfaces:
        print >> retval, print_interface(ifaces[i])

    return retval.getvalue()

def parse_args():
    if len(sys.argv) < 2:
        import os
        progname = os.path.split(sys.argv[0])[-1]
        ifaces = trac_interfaces()
        print """Usage: 
 %s <name> [interface1] [interface2] [...] # to create a component with name
 %s # for usage and component list

Interfaces available:
""" % (progname, progname)
        for key in sorted(ifaces.keys()):
            print key
        sys.exit(0)

def main():
    parse_args()
    print print_component(*sys.argv[1:])

if __name__ == '__main__':
    main()
    
