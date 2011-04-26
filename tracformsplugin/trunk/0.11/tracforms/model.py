# -*- coding: utf-8 -*-

from trac.resource import Resource, ResourceNotFound

from api import FormSystem, _

__all__ = ['Form']


class Form(object):
    """Trac resource representation of a TracForms form."""

    @staticmethod
    def id_is_valid(num):
        try:
            return 0 < int(num) <= 1L << 31
        except ValueError:
            raise ResourceNotFound(
                _("TracForm %(form_id)s does not exist.", form_id=num),
                _("Invalid form number"))

    def __init__(self, env, form_resource_or_parent_realm=None,
                 parent_id=None, subcontext=None, form_id=None, version=None):
        self.env = env
        # prepare db access
        self.forms = FormSystem(env)
        self.realm = 'form'
        self.subcontext = subcontext
        self.siblings = []
        # DEVEL: support for handling form revisions not implemented yet
        if isinstance(form_resource_or_parent_realm, Resource):
            self.resource = form_resource_or_parent_realm
            parent = self.resource.parent
            if self.siblings == []:
                self._get_siblings(parent.realm, parent.id)
        else:
            parent_realm = form_resource_or_parent_realm
            if form_id not in [None, ''] and self.id_is_valid(form_id):
                self.id = int(form_id)
            else:
                self.id = None
            if self.id is not None and (parent_realm is None or \
                    parent_id is None or subcontext is None):
                # get complete context, required as resource parent
                ctxt = self.forms.get_tracform_meta(self.id)[1:4]
                parent_realm = ctxt[0]
                parent_id = ctxt[1]
                self.subcontext = ctxt[2]
            elif isinstance(parent_realm, basestring) and \
                    parent_id is not None and self.id is None:
                # find form(s), if parent descriptors are available
                if subcontext is not None:
                    ctxt = tuple([parent_realm, parent_id, subcontext])
                    self.id = self.forms.get_tracform_meta(ctxt)[0]
            self._get_siblings(parent_realm, parent_id)
            if isinstance(parent_realm, basestring) and \
                    parent_id is not None:
                self.resource = Resource(parent_realm, parent_id
                                ).child('form', self.id, version)
            else:
                raise ResourceNotFound(
                    _("""No data recorded for a TracForms form in
                      %(realm)s:%(parent_id)s
                      """, realm=parent_realm, parent_id=parent_id),
                    subcontext and _("with subcontext %(subcontext)s",
                    subcontext=subcontext) or '')

    def _get_siblings(self, parent_realm, parent_id):
        """Add siblings list including self to form resource object."""
        self.siblings = self.forms.get_tracform_ids(tuple([parent_realm,
                                                           parent_id]))
        if len(self.siblings) == 1:
            # form_id in single form situation
            self.id = self.siblings[0][0]
            self.subcontext = self.siblings[0][1]

    @property
    def has_data(self):
        """Return whether there is any form content stored."""
        return (self.forms.get_tracform_fields(self.id) \
                .firstrow is not None or \
                self.forms.get_tracform_history(self.id) \
                .firstrow is not None or \
                self.forms.get_tracform_state(self.id) not in [None, '{}'])

