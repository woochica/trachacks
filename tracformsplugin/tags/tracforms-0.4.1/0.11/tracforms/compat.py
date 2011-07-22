# -*- coding: utf-8 -*-

# 2011 Steffen Hoffmann

"""Various classes and functions to provide backwards-compatibility with
previous versions of Python from 2.4 onward.
"""

# json was introduced in 2.6, use simplejson for older versions
# parse_qs was copied to urlparse and deprecated in cgi in 2.6
import sys
if sys.version_info[0] == 2 and sys.version_info[1] > 5:
    import json
    from urlparse import parse_qs
else:
    import simplejson as json
    from cgi import parse_qs

# A Trac issue rather than a Python one:
# Provide `resource_exists`, that has been backported to Trac 0.11.8 only.
try:
    from trac.resource import resource_exists
except ImportError:
    from trac.resource import ResourceSystem
    def resource_exists(env, resource):
        """Checks for resource existence without actually instantiating a
        model.

        :return: `True` if the resource exists, `False` if it doesn't
        and `None` in case no conclusion could be made (i.e. when
        `IResourceManager.resource_exists` is not implemented).
        """
        manager = ResourceSystem(env).get_resource_manager(resource.realm)
        if manager and hasattr(manager, 'resource_exists'):
            return manager.resource_exists(resource)
        elif resource.id is None:
            return False

