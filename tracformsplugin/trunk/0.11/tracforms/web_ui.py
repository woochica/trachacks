# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.resource import Resource, get_resource_description, \
                          get_resource_name, get_resource_url
from trac.search.api import ISearchSource, search_to_sql, shorten_result
from trac.util.datefmt import to_datetime

from model import Form
from tracdb import DBCursor
from tracforms import _
from util import format_values


class FormUI(Component):
    """Provides TracSearch support for TracForms."""

    implements(ISearchSource)

    # ISearchSource methods

    def get_search_filters(self, req):
        if 'FORM_VIEW' in req.perm:
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

