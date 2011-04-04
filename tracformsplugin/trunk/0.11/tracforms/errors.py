# -*- coding: utf-8 -*-

from tracforms import _

__all__ = ['TracFormError', 'TracFormTooManyValuesError',
           'TracFormNoOperationError', 'TracFormNoCommandError']


class TracFormError(Exception):
    def __str__(self):
        return self.message % self.args


class TracFormTooManyValuesError(TracFormError):
    def __init__(self, name):
        TracFormError.__init__(self, name)

    message = _(
        """ERROR: Too many values for TracForm variable %r
        (maybe the same field is being used multiple times?)""")


class TracFormNoOperationError(TracFormError):
    def __init__(self, name):
        TracFormError.__init__(self, name)

    message = _("ERROR: No TracForm operation '%r'")


class TracFormNoCommandError(TracFormError):
    def __init__(self, name):
        TracFormError.__init__(self, name)

    message = _("ERROR: No TracForm command '%r'")

