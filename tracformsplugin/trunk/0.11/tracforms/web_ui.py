# -*- coding: utf-8 -*-

import re

from genshi.builder import tag
from pkg_resources import resource_filename

from trac.core import Component, implements
from trac.resource import get_resource_description, \
                          get_resource_name, get_resource_url
from trac.search.api import ISearchSource, search_to_sql, shorten_result
from trac.util.datefmt import to_datetime
from trac.web.api import IRequestFilter, IRequestHandler
from trac.web.chrome import ITemplateProvider, add_ctxtnav

from api import _, tag_
from model import Form
from tracdb import DBCursor
from util import format_values, resource_from_page


class FormUI(Component):
    """Provides TracSearch support for TracForms."""

    implements(IRequestFilter, IRequestHandler, ISearchSource,
               ITemplateProvider)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        env = self.env
        page = req.path_info
        # break (recursive) search for form in forms realm
        if not page.startswith('/form') and \
                resource_from_page(env, page)[1] is not None:
            if page == '/wiki' or page == '/wiki/':
                page = '/wiki/WikiStart'
            realm, resource_id = resource_from_page(env, page)
            resource = Form(env, realm, resource_id).resource
            if 'FORM_VIEW' in req.perm:
                if resource is None:
                    # no form found
                    href = req.href.form()
                elif resource.id is None:
                    # multiple forms found
                    href = req.href.form(action='select', realm=realm,
                                         resource_id=resource_id)
                else:
                    # exactly one form found
                    href = req.href.form(resource.id, action='history')
                add_ctxtnav(req, _('Form history'), href=href,
                            title=_('Review form changes'))
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
        data['page_title'] = tag(_('History of form %(form_id)s (in ',
            form_id=form_id), tag.a(parent_name, href=parent_url), ')')
        # TRANSLATOR: Title HTML tag, usually browsers window title
        data['title'] = _('Form %(form_id)s (history)', form_id=form_id)
        data['history'] = form.get_history()
        return 'history.html', data, None

    def _do_switch(self, env, req, form):
        data = {}
        parent = form.resource.parent
        parent_name = get_resource_name(env, parent)
        parent_url = get_resource_url(env, parent, req.href)
        # TRANSLATOR: The title printed in form select page
        data['page_title'] = tag_('Form data for %(parent)s',
            parent=tag.a(parent_name, href=parent_url))
        # TRANSLATOR: Title HTML tag, usually browsers window title
        data['title'] = _('Saved forms (%(parent)s)', parent=parent_name)
        data['siblings'] = []
        for sibling in form.siblings:
            form_id = tag.a(_('Form %(form_id)s', form_id=sibling[0]),
                            href=req.href.form(sibling[0], action='history'))
            if sibling[1] == '':
                data['siblings'].append(form_id)
            else:
                data['siblings'].append(tag_(
                              "%(form_id)s (subcontext = '%(subcontext)s')",
                              form_id=form_id, subcontext = sibling[1]))
        return 'switch.html', data, None

    # ISearchSource methods

    def get_search_filters(self, req):
        if 'FORM_VIEW' in req.perm:
            # TRANSLATOR: The realm name used as TracSearch filter label
            yield ('form', _("Forms"))

    def get_search_results(self, req, terms, filters):
        if not 'form' in filters:
            return
        env = self.env
        db = env.get_db_cnx()
        cursor = DBCursor(db, self.log)
        sql, args = search_to_sql(db, ['resource_id', 'subcontext', 'author',
                                       'state', db.cast('id', 'text')], terms)
        cursor.execute("""
            SELECT id,realm,resource_id,subcontext,state,author,time
            FROM forms
            WHERE %s
            """ % (sql), *args)

        for id, realm, parent, subctxt, state, author, updated_on in cursor:
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

