# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2009 Edgewall Software
# Copyright (C) 2005-2006 Christopher Lenz <cmlenz@gmx.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
#
# Author: Christopher Lenz <cmlenz@gmx.de>

from trac.resource import ResourceSystem
from trac.util import unquote


class _RequestArgs(dict):
    """Dictionary subclass that provides convenient access to request
    parameters that may contain multiple values."""

    def getfirst(self, name, default=None):
        """Return the first value for the specified parameter, or `default` if
        the parameter was not provided.
        """
        if name not in self:
            return default
        val = self[name]
        if isinstance(val, list):
            val = val[0]
        return val

    def getlist(self, name):
        """Return a list of values for the specified parameter, even if only
        one value was provided.
        """
        if name not in self:
            return []
        val = self[name]
        if not isinstance(val, list):
            val = [val]
        return val

def parse_arg_list(query_string):
    """Parse a query string into a list of `(name, value)` tuples."""
    args = []
    if not query_string:
        return args
    for arg in query_string.split('&'):
        nv = arg.split('=', 1)
        if len(nv) == 2:
            (name, value) = nv
        else:
            (name, value) = (nv[0], empty)
        name = unquote(name.replace('+', ' '))
        if isinstance(name, str):
            name = unicode(name, 'utf-8')
        value = unquote(value.replace('+', ' '))
        if isinstance(value, str):
            value = unicode(value, 'utf-8')
        args.append((name, value))
    return args


def arg_list_to_args(arg_list):
    """Convert a list of `(name, value)` tuples into into a `_RequestArgs`."""
    args = _RequestArgs()
    for name, value in arg_list:
        if name in args:
            if isinstance(args[name], list):
                args[name].append(value)
            else:
                args[name] = [args[name], value]
        else:
            args[name] = value
    return args


def resource_exists(env, resource):
    """Checks for resource existence without actually instantiating a model.

        :return: `True` if the resource exists, `False` if it doesn't
        and `None` in case no conclusion could be made (i.e. when
        `IResourceManager.resource_exists` is not implemented).

        >>> from trac.test import EnvironmentStub
        >>> env = EnvironmentStub()

        >>> resource_exists(env, Resource('dummy-realm', 'dummy-id')) is None
        True
        >>> resource_exists(env, Resource('dummy-realm'))
        False
    """
    manager = ResourceSystem(env).get_resource_manager(resource.realm)
    if manager and hasattr(manager, 'resource_exists'):
        return manager.resource_exists(resource)
    elif resource.id is None:
        return False


class Empty(unicode):
    """A special tag object evaluating to the empty string"""
    __slots__ = []

empty = Empty()

del Empty # shouldn't be used outside of Trac core
