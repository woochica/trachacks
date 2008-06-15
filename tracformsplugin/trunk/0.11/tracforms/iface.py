
from trac.core import Interface, ExtensionPoint, Component

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

class TracFormDBUser(Component):
    tracformdb_observers = ExtensionPoint(TracFormDBObserver)

    def save_tracform(self, *_args, **_kw):
        for observer in self.tracformdb_observers:
            result = observer.save_tracform(*_args, **_kw)
            if result is not None:
                return result

    def get_tracform_meta(self, *_args, **_kw):
        for observer in self.tracformdb_observers:
            result = observer.get_tracform_meta(*_args, **_kw)
            if result is not None:
                return result

    def get_tracform_state(self, *_args, **_kw):
        for observer in self.tracformdb_observers:
            result = observer.get_tracform_state(*_args, **_kw)
            if result is not None:
                return result

    def get_tracform_history(self, *_args, **_kw):
        for observer in self.tracformdb_observers:
            result = observer.get_tracform_history(*_args, **_kw)
            if result is not None:
                return result

    def get_tracform_fieldinfo(self, *_args, **_kw):
        for observer in self.tracformdb_observers:
            result = observer.get_tracform_fieldinfo(*_args, **_kw)
            if result is not None:
                return result

    def get_tracform_fields(self, *_args, **_kw):
        for observer in self.tracformdb_observers:
            result = observer.get_tracform_fields(*_args, **_kw)
            if result is not None:
                return result

