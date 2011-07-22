# -*- coding: utf-8 -*-

import re

from genshi.builder import Markup, tag
from pkg_resources import resource_filename

from trac.core import implements
from trac.util.datefmt import format_datetime
from trac.resource import get_resource_description, \
                          get_resource_shortname, get_resource_url
from trac.search.api import ISearchSource, shorten_result
from trac.util.datefmt import to_datetime
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_ctxtnav, add_stylesheet

from api import FormDBUser, _, dgettext
from compat import json
from model import Form
from util import resource_from_page

tfpageRE = re.compile('/form(/\d+|$)')


class FormUI(FormDBUser):
    """Provides form views for reviewing and managing TracForm data.

    Extensions for the Trac web user interface display saved field values,
    metadata and history. TracSearch support for TracForms is included here
    and administrative actions to revert form changes are embedded as well.
    """

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
                req.perm(form.resource).require('FORM_RESET')
                return self._do_reset(env, req, form)

            req.perm(form.resource).require('FORM_VIEW')
            return self._do_view(env, req, form)

        if req.args.get('action') == 'select':
            realm=req.args.get('realm')
            resource_id=req.args.get('resource_id')
            if realm is not None and resource_id is not None: 
                form = Form(env, realm, resource_id)
                req.perm(form.resource).require('FORM_VIEW')
                return self._do_switch(env, req, form)

    def _do_view(self, env, req, form):
        data = {'_dgettext': dgettext}
        form_id = form.resource.id
        data['page_title'] = get_resource_description(env, form.resource,
                                                      href=req.href)
        data['title'] = get_resource_shortname(env, form.resource)
        # prime list with current state
        subcontext, author, time = self.get_tracform_meta(form_id)[3:6]
        if not subcontext == '':
            data['subcontext'] = subcontext
        state = self.get_tracform_state(form_id)
        data['fields'] = self._render_fields(form_id, state)
        history = [{'author': author, 'time': time,
                    'old_state': state}]
        # add recorded old_state
        records = self.get_tracform_history(form_id)
        for author, time, old_state in records:
            history.append({'author': author, 'time': time,
                            'old_state': old_state})
        data['history'] = parse_history(history)
        # show reset button in case of existing data and proper permission
        data['allow_reset'] = req.perm(form.resource) \
                              .has_permission('FORM_RESET') and form.has_data
        add_stylesheet(req, 'tracforms/tracforms.css')
        return 'form.html', data, None

    def _do_switch(self, env, req, form):
        data = {'_dgettext': dgettext}
        data['page_title'] = get_resource_description(env, form.resource,
                                                      href=req.href)
        data['title'] = get_resource_shortname(env, form.resource)
        data['siblings'] = []
        for sibling in form.siblings:
            form_id = tag.strong(tag.a(
                          _("Form %(form_id)s", form_id=sibling[0]),
                            href=req.href.form(sibling[0])))
            if sibling[1] == '':
                data['siblings'].append(form_id)
            else:
                # TRANSLATOR: Form list entry for form select page
                data['siblings'].append(tag(Markup(_(
                              "%(form_id)s (subcontext = '%(subcontext)s')",
                              form_id=form_id, subcontext = sibling[1]))))
        add_stylesheet(req, 'tracforms/tracforms.css')
        return 'switch.html', data, None

    def _do_reset(self, env, req, form):
        author = req.authname
        if 'rewind' in req.args:
            step = -1
        elif 'reset' in req.args:
            step = 0
        if form.resource.id is not None:
            self.reset_tracform(form.resource.id, author=author, step=step)
        else:
            self.reset_tracform(tuple([form.parent.realm, form.parent.id]),
                                author=author, step=step)
        return self._do_view(env, req, form)

    def _render_fields(self, form_id, state):
        fields = json.loads(state is not None and state or '{}')
        rendered = []
        for name, value in fields.iteritems():
            if value == 'on':
               value = _("checked (checkbox)")
            elif value == '':
               value = _("empty (text field)")
            else:
               value = '\'' + value + '\''
            author, time = self.get_tracform_fieldinfo(form_id, name)
            rendered.append(
                {'name': name, 'value': value,
                 'author': tag.span(tag(_("by %(author)s", author=author)),
                                    class_='author'),
                 'time': time is not None and tag.span(
                         format_datetime(time), class_='date') or None})
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


def parse_history(changes, fieldwise=False):
    """Versatile history parser for TracForms.

    Returns either a list of dicts for changeset display in form view or
    a dict of field change lists for stepwise form reset.
    """
    fieldhistory = {}
    history = []
    if not fieldwise == False:
        def _add_change(fieldhistory, field, author, time, old, new):
            if field not in fieldhistory.keys():
                fieldhistory[field] = [{'author': author, 'time': time,
                                        'old': old, 'new': new}]
            else:
                fieldhistory[field].append({'author': author, 'time': time,
                                            'old': old, 'new': new})
            return fieldhistory

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
            # first loop cycle: only load values for comparison next time
            new_fields = old_fields
            last_author = changeset['author']
            last_change = changeset['time']
            continue
        updated_fields = {}
        for field, old_value in old_fields.iteritems():
            new_value = new_fields.get(field)
            if new_value != old_value:
                if fieldwise == False:
                    change = _render_change(old_value, new_value)
                    if change is not None:
                        updated_fields[field] = change
                else:
                    fieldhistory = _add_change(fieldhistory, field,
                                               last_author, last_change,
                                               old_value, new_value)
        for field in new_fields:
            if old_fields.get(field) is None:
                if fieldwise == False:
                    change = _render_change(None, new_fields[field])
                    if change is not None:
                        updated_fields[field] = change
                else:
                    fieldhistory = _add_change(fieldhistory, field,
                                               last_author, last_change,
                                               None, new_fields[field])
        new_fields = old_fields
        history.append({'author': last_author,
                        'time': format_datetime(last_change),
                        'changes': updated_fields})
        last_author = changeset['author']
        last_change = changeset['time']
    return fieldwise == False and history or fieldhistory

def _render_change(old, new):
    rendered = None
    if old and not new:
        rendered = tag(Markup(_("%(value)s reset to default value",
                                value=tag.em(old))))
    elif new and not old:
        rendered = tag(Markup(_("from default value set to %(value)s",
                                value=tag.em(new))))
    elif old and new:
        if len(old) < 20 and len(new) < 20:
            rendered = tag(Markup(_("changed from %(old)s to %(new)s",
                                    old=tag.em(old), new=tag.em(new))))
        else:
            nbsp = Markup('<br />')
            # TRANSLATOR: same as before, but with additional line breaks
            rendered = tag(Markup(_("changed from %(old)s to %(new)s",
                                    old=tag.em(nbsp, old),
                                    new=tag.em(nbsp, new))))
    return rendered

def _render_values(state):
    fields = []
    for name, value in json.loads(state or '{}').iteritems():
        fields.append(name + ': ' + value)
    return '; '.join(fields)

