# -*- coding: utf-8 -*-
#
# Copyright (c) 2012, Steffen Hoffmann
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

# DEVEL: Add unit testing.

def get_target_id(target):
    """Extract the resource ID from event targets."""
    # Common Trac resource.
    if hasattr(target, 'id'):
        return str(target.id)
    # Wiki page special case.
    elif hasattr(target, 'name'):
        return target.name
    # Last resort: just stringify.
    return str(target)
