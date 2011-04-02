# -*- coding: utf-8 -*-

import sys

from trac.core import Component, ExtensionPoint, Interface, implements
from trac.resource import IResourceManager, Resource, ResourceNotFound, \
                          get_resource_name, get_resource_shortname


class TracFormDBObserver(Interface):
    def get_tracform_meta(self, src, cursor=None):
        pass

    def get_tracform_state(self, src, cursor=None):
        pass

    def get_tracform_history(self, src, cursor=None):
        pass

    def save_tracform(self, src, state, updater,
                        base_version=None, keep_history=False,
                        track_fields=False, cursor=None):
        pass

    def get_tracform_fields(self, src, cursor=None):
        pass

    def get_tracfrom_fieldinfo(self, src, field, cursor=None):
        pass


def tracob_first(fn=None, default=None):
    if fn is None:
        def builder(fn):
            return tracob_first(fn, default)
        return builder
    else:
        def wrapper(self, *_args, **_kw):
            observers = fn(self, *_args, **_kw)
            for observer in observers:
                result = getattr(observer, fn.__name__)(*_args, **_kw)
                if result is not default:
                    return result
            else:
                return default
        wrapper.__name__ = fn.__name__
        wrapper.__doc__ = fn.__doc__
        return wrapper


class TracFormDBUser(Component):
    tracformdb_observers = ExtensionPoint(TracFormDBObserver)

    @tracob_first
    def save_tracform(self, *_args, **_kw):
        return self.tracformdb_observers

    @tracob_first
    def get_tracform_meta(self, *_args, **_kw):
        return self.tracformdb_observers

    @tracob_first
    def get_tracform_state(self, *_args, **_kw):
        return self.tracformdb_observers

    @tracob_first
    def get_tracform_history(self, *_args, **_kw):
        return self.tracformdb_observers

    @tracob_first
    def get_tracform_fields(self, *_args, **_kw):
        return self.tracformdb_observers

    @tracob_first
    def get_tracform_fieldinfo(self, *_args, **_kw):
        return self.tracformdb_observers


# deferred imports to avoid circular dependencies
from formdb import TracFormDBComponent
#from model import Form


class FormSystem(Component):
    """Provides permissions and access to TracForms as resource 'form'.
    """

    implements(IResourceManager)

    # IResourceManager methods

    def get_resource_realms(self):
        yield 'form'

    def get_resource_description(self, resource, format=None, **kwargs):
        if not resource.parent:
            return 'Unparented form %s' % resource.id
        if format == 'compact':
            return '%s (%s)' % (resource.id,
                   get_resource_shortname(self.env, resource.parent))
        # DEVEL: resource description not implemented yet
        #elif format == 'summary':
        #    return Form(self.env, resource).description
        if resource.id:
            return "Form '%s' in %s" % (resource.id,
                   get_resource_name(self.env, resource.parent))
        else:
            return 'Forms of %s' % (
                   get_resource_name(self.env, resource.parent))

