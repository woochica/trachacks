from trac.core import Component, implements
from trac.perm import PermissionSystem, IPermissionRequestor
from trac.config import Option
from trac.web.api import IRequestFilter, ITemplateStreamFilter

from genshi.filters.transform import StreamBuffer
from genshi.filters import Transformer
from genshi.input import HTML


class HideableQuery(Component):

    implements(IRequestFilter, IPermissionRequestor, ITemplateStreamFilter)

    query_permission = Option(
        'hideable_query',
        'query_permission',
        default='QUERY_VIEW',
        doc='The permission which users need to see the query site')

    query_hidden_redirect = Option(
        'hideable_query',
        'query_hidden_redirect',
        default='/report',
        doc="""The site to which the user will be redirected if he has not
               the query_permission and tries to access the query site""")

    # IPermissionRequestor methods
    def get_permission_actions(self):
        group_actions = [self.query_permission]
        return group_actions

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if req.path_info.find('/query') == -1:
            return handler

        if self.query_permission in \
                PermissionSystem(self.env).get_user_permissions(req.authname):
            return handler
        else:
            if self.query_hidden_redirect == '':
                return handler
            else:
                req.redirect(self.env.href(self.query_hidden_redirect))
            return None

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename != 'query.html' and filename != 'report_list.html' and \
                       filename != 'report_view.html':
            return stream

        has_query_permission = self.query_permission in \
            PermissionSystem(self.env).get_user_permissions(req.authname)

        buffer = StreamBuffer()

        def replace_query_link():
            if has_query_permission:
                return buffer
            else:
                return HTML('<div id="ctxtnav" class="nav"></div>')

        def replace_filter_box():
            if has_query_permission:
                return buffer
            else:
                return HTML('')

        return stream | Transformer('//div[@id="ctxtnav" and @class="nav"]') \
            .copy(buffer) \
            .replace(replace_query_link).end() \
            .select('//form[@id="query" and @method="post" and @action]') \
            .copy(buffer) \
            .replace(replace_filter_box)
