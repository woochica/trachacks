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
from trac.ticket.api import ITicketChangeListener

from trac.env import open_environment

from intertrac import InterTrac

LABEL_DEPEND_PAGE = u'Dependencies'
LABEL_SUMMARY = 'Summary: '
LABEL_SUB = 'Sub: '
LABEL_PRECEDING = 'Predecessors: '
LABEL_SUBSEQUENT = 'Successors: '

TICKET_CUSTOM = "ticket-custom"

class TracDependency(Component):
    implements(IRequestHandler, IRequestFilter, ITemplateProvider, 
        ITemplateStreamFilter, ITicketManipulator, ITicketChangeListener)

    def __init__(self):
        self.project_label = self.config.get( "tracdependency", "label")
        self.log.debug("[tracdependency]:label = %s", self.project_label)
        if not self.project_label:
            self.project_label=os.path.basename(self.env.path)
            self.log.debug("base name of env_path = %s", self.project_label)
            intertrac_project_label = self.config.get( "intertrac", self.project_label+".label")
            if intertrac_project_label:
                self.project_label = intertrac_project_label
                self.log.debug("label from intertrac setting = %s", self.project_label)
        self.intertrac = InterTrac(self.config, self.env, self.project_label)

    def subsequentticket(self,ids):
        sql = ("SELECT id, type, summary, owner, description, status from ticket t "
                    "JOIN ticket_custom c ON c.ticket = t.id AND c.name = 'dependencies' "
                    "WHERE (c.value = '%s' or c.value like '%s(%%' or c.value like '%s,%%' or "
                    " c.value like '%%, %s(%%' or c.value like '%%, %s,%%' or "
                    " c.value like '%%,%s(%%' or c.value like '%%,%s,%%' or "
                    " c.value like '%%, %s' or c.value like '%%,%s')" % (ids, ids, ids, ids, ids, ids, ids, ids, ids))
        return sql
        
    def subsequentticket_i(self,ids):
        sql = ("SELECT id, type, summary, owner, description, status from ticket t "
                    "JOIN ticket_custom c ON c.ticket = t.id AND c.name = 'dependencies' "
                    "WHERE "
                    "(c.value = '%s' or c.value like '%s(%%' or c.value like '%s,%%' or "
                    " c.value like '%%, %s(%%' or c.value like '%%, %s,%%' or "
                    " c.value like '%%,%s(%%' or c.value like '%%,%s,%%' or "
                    " c.value like '%%, %s' or c.value like '%%,%s' or "
                    " c.value = '#%s' or c.value like '#%s(%%' or c.value like '#%s,%%' or "
                    " c.value like '%%, #%s(%%' or c.value like '%%, #%s,%%' or "
                    " c.value like '%%,#%s(%%' or c.value like '%%,#%s,%%' or "
                    " c.value like '%%, #%s' or c.value like '%%,#%s')" % (ids, ids, ids, ids, ids, ids, ids, ids, ids, ids, ids, ids, ids, ids, ids, ids, ids, ids))
        return sql
        
    def subticket(self, id_l):
        # InterTrac形式で指定したidを親に指定しているチケットのクエリ文字列を返す
        # id_l InterTrac形式のチケットid
        sql = ("SELECT id, type, summary, owner, description, status from ticket t "
                    "JOIN ticket_custom a ON a.ticket = t.id AND a.name = 'summary_ticket' "
                    "WHERE a.value = '%s'" % id_l)
        return sql

    def subticket_i(self, id_num):
        # 自プロジェクト内で指定したidを親に指定しているチケットのクエリ文字列を返す
        # id_num チケットのid（数値）
        sql = ("SELECT id, type, summary, owner, description, status from ticket t "
                    "JOIN ticket_custom a ON a.ticket = t.id AND a.name = 'summary_ticket' "
                    "WHERE a.value = '#%s' or  a.value = '%s'" % (id_num, id_num))
        return sql

    # IRequestHandler methods
    def match_request(self, req):
        # TODO:要確認
        return re.match(r'/dependency(?:_trac)?(?:/.*)?$', req.path_info)
    
    def process_request(self, req):
        # 依存関係の表示ページの処理
        # tkt_idは単純な数値
        tkt_id = req.path_info.split('/')[3] # '/dependency/ticket/1'のようなアドレス指定でくる．

        # tkt_idから該当するチケットの情報を取得する
        tkt = Ticket(self.env, tkt_id)
        # チケットの情報から取得できる親チケットと依存関係のリンクを作る
        summary_ticket = self.intertrac.get_link(tkt['summary_ticket'], self.log)
        dependencies = self.intertrac.get_link(tkt['dependencies'], self.log)
        # このチケットを指定している，intertracで設定されているすべてのプロジェクトからチケットを検索しリンクを作る
        tkt_id_l = self.get_project_name() + ':#' + tkt_id
        self.log.debug("self.intertrac.create_links3 %s",tkt_id_l)
        sub_ticket = self.intertrac.create_links(self.subticket(tkt_id_l), self.subticket_i(tkt_id), self.log) 
        self.log.debug("self.intertrac.create_links4 %s",tkt_id_l)
        subsequentticket = self.intertrac.create_links(self.subsequentticket(tkt_id_l), self.subsequentticket_i(tkt_id), self.log) 
        summary_ticket_enabled = not not ( self.config.get( TICKET_CUSTOM, "summary_ticket" ))
        dependencies_enabled = not not ( self.config.get( TICKET_CUSTOM, "dependencies"))
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
        if (req.path_info.startswith('/ticket/')) and data:
            # チケット表示ページの場合の処理
            # 依存ページへのリンクを作成し，このページで処理するには時間がかかるものは次のページで表示します
            href = req.href.dependency(req.path_info)
            add_ctxtnav(req, LABEL_DEPEND_PAGE, href)
            # このページのデータを置き換えるためのでデータを作成します．
            tkt = data['ticket'] # チケットのid
            tkt_id_l = self.get_project_name() + ':#' + str(tkt.id) # intertrac形式のチケット名
            sub_ticket = self.intertrac.create_links(self.subticket(tkt_id_l), self.subticket_i(str(tkt.id)), self.log)
            self.log.debug("self.intertrac.create_links2 %s",tkt_id_l)
            subsequentticket = self.intertrac.create_links(self.subsequentticket(tkt_id_l), self.subsequentticket_i(str(tkt.id)), self.log) 
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
        """チケット番号の指定に問題がないかを確認します．"""
        errors = []
        if self.config.get( TICKET_CUSTOM, "summary_ticket"): # カスタムフィールドが有効な場合
            # 親チケットが存在しているかとか指定方法に間違いがないかを確認する．
            label = self.config.get(TICKET_CUSTOM,"summary_ticket.label")
            errors.extend(self.intertrac.validate_ticket(ticket['summary_ticket'], label, False, self.log))
            # 親チケットがループしていないか確認する
            errors.extend(self.intertrac.validate_outline(ticket['summary_ticket'], ticket.id, label, self.log))
        if self.config.get( TICKET_CUSTOM, "dependencies"): # カスタムフィールドが有効な場合
            # 依存関係チケットが存在しているかとか指定方法に間違いがないかを確認する．
            label = self.config.get(TICKET_CUSTOM,"dependencies.label")
            errors.extend(self.intertrac.validate_ticket(ticket['dependencies'], label, True, self.log))
        return errors

    # ITicketChangeListener methods
    def ticket_created(self, tkt):
        pass

    def ticket_changed(self, tkt, comment, author, old_values):
        pass

    def ticket_deleted(self, tkt):
        #このチケットを指定しているチケットにコメントをつける
        pass

    def get_project_name(self):
        return self.project_label
