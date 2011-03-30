# -*- coding: utf-8 -*-

from trac.core import Component, ExtensionPoint
try:
    from acct_mgr.api import IPasswordStore
    can_check_user = True
except ImportError:
    can_check_user = False
import sys

from api import tracob_first


if can_check_user:
    class TracPasswordStoreUser(Component):
        tracpasswordstore_observers = ExtensionPoint(IPasswordStore)

        @tracob_first
        def has_user(self, *_args, **_kw):
            return self.tracpasswordstore_observers
else:
    class TracPasswordStoreUser(Component):
        def has_user(self, *_args, **_kw):
            "Stub if the user doesn't have acct_mgr installed"
            return False

