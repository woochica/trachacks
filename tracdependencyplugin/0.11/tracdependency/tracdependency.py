# -*- coding: utf-8 -*-

import re

from genshi.builder import tag
from genshi.filters.transform import Transformer

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_ctxtnav
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.ticket.model import Ticket

from trac.env import open_environment

from intertrac import InterTrac

LABEL_DEPEND_PAGE = u'Dependencies'
LABEL_SUMMARY = 'Summary: '
LABEL_SUB = 'Sub: '
LABEL_PRECEDING = 'Preceding: '
LABEL_SUBSEQUENT = 'Subsequent: '

class TracDependency(Component):
    implements(IRequestHandler, IRequestFilter, ITemplateProvider, ITemplateStreamFilter)

    def __init__(self):
        self.intertrac = InterTrac(self.config)

    def subsequentticket(self,ids):
        sql = ("SELECT id, type, summary, owner, description, status from ticket t "
                    "JOIN ticket_custom c ON c.ticket = t.id AND c.name = 'dependencies' "
                    "WHERE (c.value = '%s' or c.value like '%s(%%' or c.value like '%s,%%' or "
                    " c.value like '%%, %s(%%' or c.value like '%%, %s,%%' or "
                    " c.value like '%%, %s' )" % (ids, ids, ids, ids, ids, ids))
        return sql
        
    def subticket(self, ids):
        sql = ("SELECT id, type, summary, owner, description, status from ticket t "
                    "JOIN ticket_custom a ON a.ticket = t.id AND a.name = 'summary_ticket' "
                    "WHERE a.value = '%s'" % ids)
        return sql

    # IRequestHandler methods
    def match_request(self, req):
        return re.match(r'/dependency(?:_trac)?(?:/.*)?$', req.path_info)
    
    def process_request(self, req):
        # 依存関係の表示ページの処理
        ticket_custom = "ticket-custom"
        tkt_id = req.path_info.split('/')[3] # '/dependency/ticket/1'のようなアドレス指定でくる．

        # チケットの情報を取得する
        tkt = Ticket(self.env, tkt_id)
        # チケットの情報から取得できる親チケットと依存関係のリンクを作る
        summary_ticket = self.intertrac.get_link(tkt['summary_ticket'])
        dependencies = self.intertrac.get_link(tkt['dependencies'])
        # このチケットを指定している，intertracで設定されているすべてのプロジェクトからチケットを検索しリンクを作る
        tkt_id_l = self.env.project_name + ':#' + tkt_id
        sub_ticket = self.intertrac.create_links(self.subticket(tkt_id_l), self.log) 
        subsequentticket = self.intertrac.create_links(self.subsequentticket(tkt_id_l), self.log) 

        summary_ticket_enabled = not not ( self.config.get( ticket_custom, "summary_ticket" ))
        dependencies_enabled = not not ( self.config.get( ticket_custom, "dependencies"))
        intertracs = self.intertrac.project_information()
        custom_field = False
        return 'trac_dependency.html', {'intertracs': intertracs, 'custom_field':custom_field,
                                        'summary_ticket': summary_ticket, 'dependencies': dependencies,
                                        'sub_ticket': sub_ticket, 'subsequentticket': subsequentticket,
                                        'summary_ticket_enabled': summary_ticket_enabled,
                                        'dependencies_enabled':dependencies_enabled }, None
   
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
         
    def post_process_request(self, req, template, data, content_type):
        # ページのアドレスは/dependency/ticket/1
        if (req.path_info.startswith('/ticket')) and data:
            # チケット表示ページの場合の処理
            # 依存ページへのリンクを作成し，このページで処理するには時間がかかるものは次のページで表示します
            href = req.href.dependency(req.path_info)
            add_ctxtnav(req, LABEL_DEPEND_PAGE, href)
            # このページのデータを置き換えるためのでデータを作成します．
            tkt = data['ticket']
            tkt_id_l = self.env.project_name + ':#' + str(tkt.id)
            sub_ticket = self.intertrac.create_links(self.subticket(tkt_id_l), self.log)
            subsequentticket = self.intertrac.create_links(self.subsequentticket(tkt_id_l), self.log) 
            data['tracdependency'] = {
                'field_values': {
                    'summary_ticket': self.intertrac.linkify_ids(self.env, req, tkt['summary_ticket'],LABEL_SUMMARY ,LABEL_SUB ,sub_ticket, self.log),
                    'dependencies': self.intertrac.linkify_ids(self.env, req, tkt['dependencies'],LABEL_PRECEDING ,LABEL_SUBSEQUENT , subsequentticket, self.log),
                },
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
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename('tracdependency', 'templates')]