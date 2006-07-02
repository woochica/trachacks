# Utility functions

__all__ = ['any', 'find']


# List utilities
def any(list, fn):
    for val in list:
        if fn(val):
            return True
    return False

def find(list, fn):
    for val in list:
        if fn(val):
            return val
    return None
    
