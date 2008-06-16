
from trac.core import Interface, ExtensionPoint, Component
from acct_mgr.api import IPasswordStore
import sys

class TracFormDBObserver(Interface):
    def get_tracform_meta(self, src, cursor=None):
        pass

    def get_tracform_state(self, src, cursor=None):
        pass

    def get_tracform_history(self, src, cursor=None):
        pass

    def save_tracform(self, src, state, updater,
                        base_version=None, keep_history=True,
                        track_fields=True, cursor=None):
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

class TracPasswordStoreUser(Component):
    tracpasswordstore_observers = ExtensionPoint(IPasswordStore)

    @tracob_first
    def has_user(self, *_args, **_kw):
        return self.tracpasswordstore_observers

