# -*- coding: utf-8 -*-

from trac.resource import Resource, ResourceNotFound
from trac.util.datefmt import format_datetime

from api import FormSystem, _

__all__ = ['Form']


class Form(object):
    """Trac resource representation of a TracForms form."""

    @staticmethod
    def id_is_valid(num):
        return 0 < int(num) <= 1L << 31

    def __init__(self, env, form_resource_or_parent_realm=None,
                 parent_id=None, subcontext=None, form_id=None, version=None):
        # prepare db access
        self.forms = FormSystem(env)
        self.subcontext = subcontext
        self.siblings = None
        # DEVEL: support for handling form revisions not implemented yet
        if isinstance(form_resource_or_parent_realm, Resource):
            self.resource = form_resource_or_parent_realm
        else:
            parent_realm = form_resource_or_parent_realm
            if form_id is not None:
                try:
                    if self.id_is_valid(form_id):
                        self.form_id = int(form_id)
                except ValueError:
                    raise ResourceNotFound(
                        _('TracForm %(id)s does not exist.', id=form_id),
                        _('Invalid form number'))
            else:
                self.form_id = None
            if self.form_id is not None and (parent_realm is None or \
                    parent_id is None):
                # get complete context, required as resource parent
                ctxt = self.forms.get_tracform_meta(self.form_id)[1:4]
                parent_realm = ctxt[0]
                parent_id = ctxt[1]
                self.subcontext = ctxt[2]
            elif isinstance(parent_realm, basestring) and \
                    parent_id is not None and self.form_id is None:
                # find form_id, if parent descriptors are available
                if subcontext is None:
                    self.siblings = self.forms.get_tracform_ids(
                                   tuple([parent_realm, parent_id]))
                    if len(self.siblings) == 1:
                        subcontext = self.siblings[0][1]
                ctxt = tuple([parent_realm, parent_id, subcontext])
                form_id = self.forms.get_tracform_meta(ctxt)[0]
                if form_id is not None:
                    self.form_id = int(form_id)
            if isinstance(parent_realm, basestring) and \
                    parent_id is not None: # and self.form_id is not None:
                self.resource = Resource(parent_realm, parent_id
                                ).child('form', self.form_id, version)
            else:
                raise ResourceNotFound(
                    _("""No data recorded for a TracForms form in
                      %(realm)s:%(parent_id)s
                      """, realm=parent_realm, parent_id=parent_id),
                    subcontext and _('with subcontext %(subcontext)s',
                    subcontext=subcontext) or '')

                self.resource = None
                self.form_id = None
                self.parent_realm = None
                self.parent_id = None
                self.siblings = None
        if self.resource is not None:
            self.parent_realm = self.resource.parent.realm
            self.parent_id = self.resource.parent.id
            if self.siblings is None:
                self.siblings = self.forms.get_tracform_ids(
                               tuple([parent_realm, parent_id]))
                if len(self.siblings) == 1:
                    self.subcontext = self.siblings[0][1]
        self.env = env

    def get_history(self):
        """Return recorded old states of current form."""
        history = []
        records = self.forms.get_tracform_history(self.form_id)
        for author, time, old_state in records:
            history.append({'author': author, 'time': format_datetime(time),
                            'old_state': old_state})
        return history

