# -*- coding: utf-8 -*-

class TracFormError(Exception):
    def __str__(self):
        return self.message % self.args

class TracFormTooManyValuesError(TracFormError):
    def __init__(self, name):
        TracFormError.__init__(self, name)

    message = ('ERROR: Too many values for TracForm variable %r' +
        ' (maybe the same field is being used multiple times?)')

class TracFormNoOperationError(TracFormError):
    def __init__(self, name):
        TracFormError.__init__(self, name)

    message = 'ERROR: No TracForm operation named %r'

class TracFormNoCommandError(TracFormError):
    def __init__(self, name):
        TracFormError.__init__(self, name)

    message = 'ERROR: No TracForm command named %r'

