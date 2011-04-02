# -*- coding: utf-8 -*-

from trac.resource import Resource

__all__ = ['Form']


class Form(object):
    """Trac resource representation of a TracForm.
    """

    @staticmethod
    def id_is_valid(num):
        return 0 < int(num) <= 1L << 31

    def __init__(self, env, form_resource_or_parent_realm=None,
                 parent_id=None, context=None, form_id=None, version=None):
        # DEVEL: support for handling form revisions not implemented yet
        if isinstance(form_resource_or_parent_realm, Resource):
            self.resource = form_resource_or_parent_realm
        elif form_id is not None:
            if isinstance(form_resource_or_parent_realm, basestring) and \
                parent_id is not None:
                    self.resource = Resource(form_resource_or_parent_realm,
                                             parent_id
                                    ).child('form', form_id, version)
            else:
                self.resource = None
        self.env = env

