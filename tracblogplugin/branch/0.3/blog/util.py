# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 John Hampton <pacopablo@asylumware.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at:
# http://trac-hacks.org/wiki/TracBlogPlugin
#
# Author: John Hampton <pacopablo@asylumware.com>

import re

__all__ = ['bool_val', 'list_val']

BOOLS_TRUE = ['true', 'yes', 'ok', 'on', 'enabled', '1']
_list_split = re.compile('[,\s]+')

def bool_val(val):
    """Converts the val to a boolean value"""
    global BOOLS_TRUE

    if isinstance(val, bool):
        return val
    if isinstance(val, (str, unicode)):
        return val.strip().lower() in BOOLS_TRUE
    return None           
                        
def list_val(val):  
    """Converts the value into a list of values.
                
    Both commas and whitespace are considered valid separators of list elements.
                                                                
    """
    global _list_split

    if isinstance(val, basestring):
        return [t.strip() for t in _list_split.split(val) if t.strip()]
    return [val]

