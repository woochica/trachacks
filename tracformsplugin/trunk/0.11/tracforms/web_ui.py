# -*- coding: utf-8 -*-

import re

from genshi.builder import tag
from pkg_resources import resource_filename

from trac.core import implements
from trac.util.datefmt import format_datetime
from trac.resource import get_resource_description, \
                          get_resource_shortname, get_resource_url
from trac.search.api import ISearchSource, shorten_result
from trac.util.datefmt import to_datetime
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_ctxtnav, add_stylesheet

from api import FormDBUser, _, tag_
from compat import json
from model import Form
from tracdb import DBCursor
from util import resource_from_page

tfpageRE = re.compile('/form(/\d+|$)')
 

class FormUI(FormDBUser):
    """Provides TracSearch support for TracForms."""

    implements(IRequestFilter, IRequestHandler, ISearchSource,
               ITemplateProvider)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        env = self.env
        page = req.path_info
        realm, resource_id = resource_from_page(env, page)
        # break (recursive) search for form in forms realm
        if tfpageRE.match(page) == None and resource_id is not None:
            if page == '/wiki' or page == '/wiki/':
                page = '/wiki/WikiStart'
            form = Form(env, realm, resource_id)
            if 'FORM_VIEW' in req.perm(form.resource):
                if len(form.siblings) == 0:
                    # no form record found for this parent resource
                    href = req.href.form()
                    return (template, data, content_type)
                elif form.resource.id is not None:
                    # single form record found
                    href = req.href.form(form.resource.id)
                else:
                    # multiple form records found
                    href = req.href.form(action='select', realm=realm,
                                         resource_id=resource_id)
                add_ctxtnav(req, _("Form details"), href=href,
                            title=_("Review form data"))
        elif page.startswith('/form') and not resource_id == '':
            form = Form(env, form_id=resource_id)
            parent = form.resource.parent
            if len(form.siblings) > 1:
                href = req.href.form(action='select', realm=parent.realm,
                                     resource_id=parent.id)
                add_ctxtnav(req, _("Back to forms list"), href=href)
        return (template, data, content_type)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        """Return static resources for TracForms."""
        return [('tracforms', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return template directory for TracForms."""
        return [resource_filename(__name__, 'templates')]

    # IRequestHandler methods

    def match_request(self, req):
        if req.path_info == '/form':
            return True
        match = re.match('/form/(\d+)$', req.path_info)
        if match:
            if match.group(1):
                req.args['id'] = match.group(1)
            return True

    def process_request(self, req):
        env = self.env
        id_hint = req.args.get('id')
        if id_hint is not None and Form.id_is_valid(id_hint):
            form_id = int(id_hint)
        else:
            form_id = None
        if form_id is not None:
            form = Form(env, form_id=form_id)
            if req.method == 'POST':
                if req.args.get('action') == 'reset':
                    req.perm(form.resource).require('FORM_RESET')
                    return self._do_reset(env, req, form)

            req.perm(form.resource).require('FORM_VIEW')
            return self._do_history(env, req, form)

        if req.args.get('action') == 'select':
            realm=req.args.get('realm')
            resource_id=req.args.get('resource_id')
            if realm is not None and resource_id is not None: 
                form = Form(env, realm, resource_id)
                req.perm(form.resource).require('FORM_VIEW')
                return self._do_switch(env, req, form)

    def _do_history(self, env, req, form):
        data = {}
        form_id = form.resource.id
        data['page_title'] = get_resource_description(env, form.resource,
                                                      href=req.href)
        data['title'] = get_resource_shortname(env, form.resource)
        # prime list with current state
        author, time = self.get_tracform_meta(form_id)[4:6]
        state = self.get_tracform_state(form_id)
        history = [{'author': author, 'time': time,
                    'old_state': state}]
        # add recorded old_state
        records = self.get_tracform_history(form_id)
        for author, time, old_state in records:
            history.append({'author': author, 'time': time,
                            'old_state': old_state})
        data['history'] = self._render_history(history)
        # show reset button in case of existing data and proper permission
        data['allow_reset'] = req.perm(form.resource) \
                              .has_permission('FORM_RESET') and \
                              self.get_tracform_fields(form_id) \
                              .firstrow is not None
        add_stylesheet(req, 'tracforms/tracforms.css')
        return 'form.html', data, None

    def _do_switch(self, env, req, form):
        data = {}
        data['page_title'] = get_resource_description(env, form.resource,
                                                      href=req.href)
        data['title'] = get_resource_shortname(env, form.resource)
        data['siblings'] = []
        for sibling in form.siblings:
            form_id = tag.strong(tag.a(_("Form %(form_id)s",
                                         form_id=sibling[0]),
                                         href=req.href.form(sibling[0])))
            if sibling[1] == '':
                data['siblings'].append(form_id)
            else:
                # TRANSLATOR: Form list entry for form select page
                data['siblings'].append(tag_(
                              "%(form_id)s (subcontext = '%(subcontext)s')",
                              form_id=form_id, subcontext = sibling[1]))
        add_stylesheet(req, 'tracforms/tracforms.css')
        return 'switch.html', data, None

    def _do_reset(self, env, req, form):
        author = req.authname
        if form.resource.id is not None:
            self.reset_tracform(form.resource.id, author=author)
        else:
            self.reset_tracform(
                tuple([form.parent.realm, form.parent.id]), author=author)
        return self._do_switch(env, req, form)

    def _render_history(self, changes):
        history = []
        new_fields = None
        for changeset in changes:
            # break down old and new version
            try:
                old_fields = json.loads(changeset.get('old_state', '{}'))
            except ValueError:
                # skip invalid history
                old_fields = {}
                pass
            if new_fields is None:
                new_fields = old_fields
                last_change = changeset['time']
                continue
            updated_fields = []
            for field, old_value in old_fields.iteritems():
                if new_fields.get(field) != old_value:
                    change = self._render_change(old_value,
                                                 new_fields.get(field))
                    if change is not None:
                        updated_fields.append({'field': tag.strong(field),
                                               'change': change})
            for field in new_fields:
                if old_fields.get(field) is None:
                    change = self._render_change(None, new_fields[field])
                    if change is not None:
                        updated_fields.append({'field': tag.strong(field),
                                               'change': change})
            new_fields = old_fields
            history.append({'author': changeset['author'],
                            'time': format_datetime(last_change),
                            'changes': updated_fields})
            last_change = changeset['time']
        return history

    def _render_change(self, old, new):
        rendered = None
        if old and not new:
            rendered = tag_("%(value)s reset to default value",
                                value=tag.em(old))
        elif new and not old:
            rendered = tag_("from default value set to %(value)s",
                                value=tag.em(new))
        elif old and new:
            rendered = tag_("changed from %(old)s to %(new)s",
                                old=tag.em(old), new=tag.em(new))
        return rendered

    # ISearchSource methods

    def get_search_filters(self, req):
        if 'FORM_VIEW' in req.perm:
            # TRANSLATOR: The realm name used as TracSearch filter label
            yield ('form', _("Forms"))

    def get_search_results(self, req, terms, filters):
        if not 'form' in filters:
            return
        env = self.env
        results = self.search_tracforms(env, terms)

        for id, realm, parent, subctxt, state, author, updated_on in results:
            # DEVEL: support for handling form revisions not implemented yet
            #form = Form(env, realm, parent, subctxt, id, version)
            form = Form(env, realm, parent, subctxt, id)
            if 'FORM_VIEW' in req.perm(form):
                form = form.resource
                # build a more human-readable form values representation,
                # especially with unicode character escapes removed
                state = _render_values(state)
                yield (get_resource_url(env, form, req.href),
                       get_resource_description(env, form),
                       to_datetime(updated_on), author,
                       shorten_result(state, terms))


def _render_values(state):
    fields = []
    for name, value in json.loads(state or '{}').iteritems():
        fields.append(name + ': ' + value)
    return '; '.join(fields)

