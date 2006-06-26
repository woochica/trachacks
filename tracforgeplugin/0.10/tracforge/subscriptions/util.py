# TracForge utility functions

from trac.env import Environment

import os, os.path

__all__ = ['open_env','serialize_map','unserialize_map']

def open_env(path):
    """Open another Environment."""
    if isinstance(path,Environment):
        return path # Just in case
    elif '/' not in path:
        raise Exception, "Don't do this yet"
        head, tail = os.path.split(myenv.path)
        newpath = os.path.join(tail,path)
        return Environment(newpath)
    else:
        return Environment(path)

def serialize_map(linkmap):
    data = []
    for k,v in linkmap.iteritems():
        data.append(k)
        data.append(str(v))
    return os.pathsep.join(data)
    
def unserialize_map(string):
    data = string.split(os.pathsep)
    linkmap = {}
    for i in range(0,len(data),2):
        linkmap[data[i]] = int(data[i+1])
    return linkmap
