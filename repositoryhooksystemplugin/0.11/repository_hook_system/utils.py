"""
generic utilities needed for the RepositoryHookSystem package;
ideally, these would be part of python's stdlib, but until then,
roll one's own
"""

import os
import subprocess
import sys

def iswritable(filename):
    """
    returns whether or not a filename is writable,
    irregardless of its existance
    """

    if os.path.exists(filename):
        return os.access(filename, os.W_OK)
    else:
        
        # XXX try to make the file and delete it,
        # as this is easier than figuring out permissions
        try:
            file(filename, 'w').close()
        except IOError:
            return False

        os.remove(filename) # remove the file stub
        return True

def command_line_args(string):
    p = subprocess.Popen('%s %s %s' % (sys.executable, 
                                       os.path.abspath(__file__),
                                       string),
                         shell=True, stdout=subprocess.PIPE)
    stdout = p.communicate()[0]
    args = stdout.split('\n')[:-1]
    return args

if __name__ == '__main__':
    for i in sys.argv[1:]:
        print i
