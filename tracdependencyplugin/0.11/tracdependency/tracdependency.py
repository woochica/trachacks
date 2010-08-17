# -*- coding: utf-8 -*-

import re
import os.path

from genshi.builder import tag
from genshi.filters.transform import Transformer

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_ctxtnav
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.ticket.model import Ticket
from trac.ticket.api import ITicketManipulator
# from trac.ticket.api import ITicketChangeListener

from trac.env import open_environment

from intertrac import InterTrac

LABEL_DEPEND_PAGE = u'Dependencies'

TICKET_CUSTOM = "ticket-custom"

class TracDependency(Component, InterTrac):
    implements(IRequestHandler, IRequestFilter, ITemplateProvider, 
        ITemplateStreamFilter, ITicketManipulator)

    def __init__(self):
        self.project_label = self.config.get( "tracdependency", "label")
        if not self.project_label:
            self.project_label=os.path.basename(self.env.path)
            intertrac_project_label = self.config.get( "intertrac", self.project_label+".label")
            if intertrac_project_label:
                self.project_label = intertrac_project_label
        # self.load_intertrac_setting()

    # IRequestHandler methods
    def match_request(self, req):
        # TODO:要確認
        return re.match(r'/dependency(?:_trac)?(?:/.*)?$', req.path_info)
    
    def process_request(self, req):
        # 依存関係の表示ページの処理
        # tkt_idは単純な数値
        # '/dependency/ticket/1'のようなアドレス指定でくる．
        tkt_id = req.path_info.split('/')[3]
        return 'trac_dependency.html', self.get_dependency_info(tkt_id), None
   
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
         
    def post_process_request(self, req, template, data, content_type):
        # ページのアドレスは/ticket/1
        if (req.path_info.startswith('/ticket/')) and data:
            # チケット表示ページの場合の処理
            # 依存ページへのリンクを作成し，このページで処理するには時間がかかるものは次のページで表示します
            href = req.href.dependency(req.path_info)
            add_ctxtnav(req, LABEL_DEPEND_PAGE, href)
            field_values = self.get_dependency_field_values(data['ticket'])
            data['tracdependency'] = {
                'field_values': field_values
            }
        return template, data, content_type

    FIELD_XPATH = 'div[@id="ticket"]/table[@class="properties"]/td[@headers="h_%s"]/text()'

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        # 実際の置き換えを行います．
        if 'tracdependency' in data:
            for field, value in data['tracdependency']['field_values'].iteritems():
                stream |= Transformer(self.FIELD_XPATH % field).replace(value)
        return stream

    #ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('static', resource_filename('tracdependency', 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename('tracdependency', 'templates')]

    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        pass

    def validate_ticket(self, req, ticket):
        return self.validate_ticket_b(ticket)

#    # ITicketChangeListener methods
#    def ticket_created(self, tkt):
#        pass
#
#    def ticket_changed(self, tkt, comment, author, old_values):
#        pass
#
#    def ticket_deleted(self, tkt):
#        #このチケットを指定しているチケットにコメントをつける
#        pass
