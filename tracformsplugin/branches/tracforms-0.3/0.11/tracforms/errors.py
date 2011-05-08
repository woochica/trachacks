# -*- coding: utf-8 -*-

from api import _

__all__ = ['FormError', 'FormTooManyValuesError',
           'FormNoOperationError', 'FormNoCommandError']


class FormError(Exception):
    def __str__(self):
        return self.message % self.args


class FormTooManyValuesError(FormError):
    def __init__(self, name):
        FormError.__init__(self, name)

    message = _(
        """ERROR: Too many values for TracForms form variable %r
        (maybe the same field is being used multiple times?)""")


class FormNoOperationError(FormError):
    def __init__(self, name):
        FormError.__init__(self, name)

    message = _("ERROR: No TracForms operation '%r'")


class FormNoCommandError(FormError):
    def __init__(self, name):
        FormError.__init__(self, name)

    message = _("ERROR: No TracForms command '%r'")

