# -*- coding: utf-8 -*-

import re

from genshi.builder import tag
from pkg_resources import resource_filename

from trac.core import implements
from trac.util.datefmt import format_datetime
from trac.resource import get_resource_description, \
                          get_resource_name, get_resource_url
from trac.search.api import ISearchSource, shorten_result
from trac.util.datefmt import to_datetime
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_ctxtnav, add_stylesheet

from api import FormDBUser, _, tag_
from compat import json
from model import Form
from tracdb import DBCursor
from util import format_values, resource_from_page


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
        if not page.startswith('/form') and resource_id is not None:
            if page == '/wiki' or page == '/wiki/':
                page = '/wiki/WikiStart'
            resource = Form(env, realm, resource_id).resource
            if 'FORM_VIEW' in req.perm:
                if resource is None or len(self.get_tracform_ids(
                                    tuple([realm, resource_id]))) == 0:
                    # no form found
                    href = req.href.form()
                    return (template, data, content_type)
                elif resource.id is not None:
                    # exactly one form found
                    href = req.href.form(resource.id, action='history')
                else:
                    # multiple forms found
                    href = req.href.form(action='select', realm=realm,
                                         resource_id=resource_id)
                add_ctxtnav(req, _("Form history"), href=href,
                            title=_("Review form changes"))
        elif page.startswith('/form') and req.args.get('action') == 'history':
            form = Form(env, form_id=resource_id)
            if len(form.siblings) > 1:
                href = req.href.form(action='select',
                    realm=form.parent_realm, resource_id=form.parent_id)
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
        form_id = req.args.get('id')
        if form_id is not None:
            form = Form(env, form_id=form_id)
            req.perm(form).require('FORM_VIEW')
            if req.args.get('action') == 'history':
                return self._do_history(env, req, form)

            if req.method == 'POST':
                req.perm(form).require('FORM_RESET')
                if req.args.get('action') == 'reset':
                    return self._do_reset(env, req, form)

        realm=req.args.get('realm')
        resource_id=req.args.get('resource_id')
        if realm is not None and resource_id is not None: 
            form = Form(env, realm, resource_id)
            req.perm(form).require('FORM_VIEW')
            if req.args.get('action') == 'select':
                return self._do_switch(env, req, form)

    def _do_history(self, env, req, form):
        data = {}
        form_id = req.args.get('id')
        parent = form.resource.parent
        parent_name = get_resource_name(env, parent)
        parent_url = get_resource_url(env, parent, req.href)
        # TRANSLATOR: The title printed in form history page
        data['page_title'] = tag_("Form %(form_id)s (in %(parent)s)",
            form_id=form_id, parent=tag.a(parent_name, href=parent_url))
        # TRANSLATOR: Title HTML tag, usually browsers window title
        data['title'] = _("Form %(form_id)s (history)", form_id=form_id)
        author, time = self.get_tracform_meta(int(form_id))[4:6]
        state = self.get_tracform_state(int(form_id))
        history = [{'author': author, 'time': time,
                    'old_state': state}]
        history.extend(form.get_history())
        data['history'] = self._render_history(history)
        data['allow_reset'] = (req.perm.has_permission('FORM_RESET') and \
            self.get_tracform_fields(int(form_id)).firstrow is not None)
        add_stylesheet(req, 'tracforms/tracforms.css')
        return 'history.html', data, None

    def _do_switch(self, env, req, form):
        data = {}
        parent = form.resource.parent
        parent_name = get_resource_name(env, parent)
        parent_url = get_resource_url(env, parent, req.href)
        # TRANSLATOR: The title printed in form select page
        data['page_title'] = tag_("Forms in %(parent)s",
            parent=tag.a(parent_name, href=parent_url))
        # TRANSLATOR: Title HTML tag, usually browsers window title
        data['title'] = _("Forms (%(parent)s)", parent=parent_name)
        data['siblings'] = []
        for sibling in form.siblings:
            form_id = tag.strong(tag.a(_("Form %(form_id)s",
                                         form_id=sibling[0]),
                                         href=req.href.form(sibling[0],
                                                       action='history')))
            if sibling[1] == '':
                data['siblings'].append(form_id)
            else:
                data['siblings'].append(tag_(
                              "%(form_id)s (subcontext = '%(subcontext)s')",
                              form_id=form_id, subcontext = sibling[1]))
        add_stylesheet(req, 'tracforms/tracforms.css')
        return 'switch.html', data, None

    def _do_reset(self, env, req, form):
        author = req.authname
        if form.form_id is not None:
            self.reset_tracform(form.form_id, author=author)
        else:
            self.reset_tracform(
                tuple([form.parent_realm, form.parent_id]), author=author)
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
                state = format_values(state)
                yield (get_resource_url(env, form.parent, req.href),
                       get_resource_description(env, form),
                       to_datetime(updated_on), author,
                       shorten_result(state, terms))

