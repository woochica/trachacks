# TracForge utility functions

from trac.env import Environment

import os.path

__all__ = ['open_env']

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
