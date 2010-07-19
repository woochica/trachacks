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

from trac.env import open_environment

LABEL_SUMMARY = u'Summary: '
LABEL_SUB = u'Sub: '
LABEL_PRECEDING = u'Predecessors: '
LABEL_SUBSEQUENT = u'Successors: '
ERROE_MSG1 = u' project %s does not exist.'
ERROE_MSG2 = u'Unknown type of dependency.'
ERROE_MSG3 = u'Ticket(%s)\'s summary ticket is this ticket'
ERROE_MSG4 = u'There is no ticket %s(prj=%s,id=%s).'
ERROE_MSG5 = u'Many comma are in this field.'
ERROE_MSG6 = u'Ticekt not exists'
ERROE_MSG7 = u'This field can not have dependency.'
IT_ERROR_MSG1 = u"Project(%s) is normal type intertrac project."
IT_ERROR_MSG2 = u"Can not open project db %s."
IT_ERROR_MSG3 = u"Project(%s) has not url."
IT_ERROR_MSG4 = u"Project(%s) has no label, so automaticaly set this projects label to %s."

TICKET_CUSTOM = "ticket-custom"

class InterTrac:

    def load_intertrac_setting(self):
        # interTracの設定を取得します．
        self.intertracs0 = {}
        self.summary_label = self.config.get(TICKET_CUSTOM,"summary_ticket.label")
        self.dependencies_label = self.config.get(TICKET_CUSTOM,"dependencies.label")
        for key, value in self.config.options('intertrac'):
            # オプションの数のループを回り，左辺値の.を探します．
            idx = key.rfind('.')  
            if idx > 0: # .が無い場合はショートカットですが無視します
                # .があった場合の処理
                # 左辺値を分割します
                prefix, attribute = key[:idx], key[idx+1:]
                # すでにあるものをとってきます無ければ新規で作成
                intertrac = self.intertracs0.setdefault(prefix, {})
                # 左辺値のピリオド以降をキーで右辺値を登録
                intertrac[attribute] = value
                # プロジェクト名を設定します．(注：すべて小文字になっている) 
                intertrac['name'] = prefix
        keys = self.intertracs0.keys()
        for key in keys:
            intertrac = self.intertracs0[key]
            path = intertrac.get('path', '')
            label = intertrac.get('label', '')
            url = intertrac.get('url', '')
            if path == '':
                self.log.debug(IT_ERROR_MSG1, key)
                del self.intertracs0[key]
            elif url == '':
                self.log.debug(IT_ERROR_MSG3, key)
                del self.intertracs0[key]
            elif label == '':
                label = os.path.basename(self.env.path)
                self.log.debug(IT_ERROR_MSG4, key, label)
                self.config.set('intertrac', key + '.label', label)
            else:
                # trac.iniをオープンする
                try:
                    if self.__get_project_name() != label:
                        project = open_environment(path, use_cache=True)
                except Exception, e:
                    self.log.error(IT_ERROR_MSG2, key)
                    del self.intertracs0[key]

    def __get_projects(self):
        return self.intertracs0

    def __get_subsequentticket_other_prj(self,ids):
        sql = ("SELECT id, type, summary, owner, description, status from ticket t "
                    "JOIN ticket_custom c ON c.ticket = t.id AND c.name = 'dependencies' "
                    "WHERE (c.value = '%s' or c.value like '%s(%%' or c.value like '%s,%%' or "
                    " c.value like '%%, %s(%%' or c.value like '%%, %s,%%' or "
                    " c.value like '%%,%s(%%' or c.value like '%%,%s,%%' or "
                    " c.value like '%%, %s' or c.value like '%%,%s')" % (ids, ids, ids, ids, ids, ids, ids, ids, ids))
        return sql
        
    def __get_subsequentticket(self,ids):
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
        
    def __get_subticket_other_prj(self, id_l):
        # InterTrac形式で指定したidを親に指定しているチケットのクエリ文字列を返す
        # id_l InterTrac形式のチケットid
        sql = ("SELECT id, type, summary, owner, description, status from ticket t "
                    "JOIN ticket_custom a ON a.ticket = t.id AND a.name = 'summary_ticket' "
                    "WHERE a.value = '%s'" % id_l)
        return sql

    def __get_subticket(self, id_num):
        # 自プロジェクト内で指定したidを親に指定しているチケットのクエリ文字列を返す
        # id_num チケットのid（数値）
        sql = ("SELECT id, type, summary, owner, description, status from ticket t "
                    "JOIN ticket_custom a ON a.ticket = t.id AND a.name = 'summary_ticket' "
                    "WHERE a.value = '#%s' or  a.value = '%s'" % (id_num, id_num))
        return sql

    def __get_tickets_point_to(self, sql, sql_i):
        # InterTrac設定しているプロジェクトすべてを検索する必要がある,
        # 後続チケットまたは，子チケットへのリンクを作ります．
        links = []
        intertracs0 = self.__get_projects()
        # すべてのinterTrc設定を回りサブチケットまたは後続チケットを探します．まずはInterTrac形式の指定のもの
        for prefix in intertracs0:
            intertrac = intertracs0[prefix]
            path = intertrac.get('path', '')
            try:
                if self.__get_project_name() == intertrac['label']:
                    cursor = self.env.get_db_cnx().cursor()
                    cursor.execute(sql_i + " union " + sql)
                    id_prefix = '#'
                else:
                    cursor = open_environment(path, use_cache=True).get_db_cnx().cursor()
                    cursor.execute(sql)
                    id_prefix = intertrac['label'] + ':#' + str(id)
                for id, type, summary, owner, description, status in cursor:
                    url = intertrac.get('url', '') + '/ticket/' + str(id)
                    dep_url = intertrac.get('url', '') + '/dependency/ticket/' + str(id)
                    ticket = id_prefix + str(id)
                    links.append({'ticket':ticket, 'title':summary, 'url':url, 'dep_url':dep_url, 'status':status})
                    # links.append({'title':summary, 'url':url, 'dep_url':dep_url, 'status':status})
            except Exception, e:
                pass
            # オープンできない場合もあるのでエラー処理が必要
        return links

    def __get_intertrac_ticket(self, ticket, dep_en):
        # 指定されたInterTrac形式のチケット名から情報を取得する
        # 問題があった場合はエラーを返す．
        current_project_name = self.__get_project_name()
        intertracs0 = self.__get_projects()
        if ticket:
            ticket = ticket.strip() # 前後の空白を削除します
            idx = ticket.rfind(':#') # プロジェクト名とチケット番号に分割します
            if idx > 0: # InterTrac ticket
                current_project = False
                project_name, id = ticket[:idx], ticket[idx+2:]
                # プロジェクト名が存在するか確認する
                try:
                    intertrac = intertracs0[project_name.lower()]
                except Exception, e: # 存在していない場合は例外が発生する
                    return {'error' : ERROE_MSG1 % project_name}
            else: # This ticket is in same project.
                current_project = True
                project_name = current_project_name
                if ticket.rfind('#') == 0:
                    id = ticket[1:]
                else:
                    id = ticket
            if id != "":
                # 依存関係を指定しているか確認する 例:(FF)
                idx = id.rfind('(')
                if idx > 0:
                    # 指定されていたならそれはidに含まない
                    if dep_en == False:
                        #依存関係を使用しない場合でカッコがあった場合は
                        return {'error' : ERROE_MSG7}
                    id, dep = id[:idx], id[idx+1:]
                    #依存関係に問題がないかの確認が必要
                    if dep.startswith('FF')==False and dep.startswith('FS')==False and dep.startswith('SF')==False and dep.startswith('SS')==False:
                        return {'error' : ERROE_MSG2}
                else:
                    dep = ''
                try:
                    # InterTracの設定のキーは小文字
                    intertrac = intertracs0[project_name.lower()]
                    path = intertrac.get('path', '')
                    project = open_environment(path, use_cache=True)
                    tkt = Ticket(project, id)
                    url = intertrac.get('url', '') + '/ticket/' + id
                    dep_url = intertrac.get('url', '') + '/dependency/ticket/' + id
                except Exception, e:
                    return {'error' : ERROE_MSG4 % (ticket, project_name, id)}
            else: #チケットに何も入っていない
                return {'error' : ERROE_MSG5}
            return {'name':project_name+':#'+id, 'url':url, 'dep_url':dep_url, 'error':None, 'ticket':tkt}
        else:
            return {'error': ERROE_MSG6}

    def __validate_outline_b(self, ticket, sub_ticket, leaf_id):
        # tkt:InterTrac形式のチケット名
        # project_name:葉チケットのプロジェクト名
        # leaf_id:葉チケットのID
        # 戻り値:エラー文字列
        error = []
        if ticket:
            ticket = ticket.strip() # 前後の空白を削除します
        if ticket == leaf_id:
            return ERROE_MSG3 % sub_ticket
        t = self.__get_intertrac_ticket(ticket, False)
        error = t['error']
        if error is None:
            tkt = t['ticket']
            ticket = tkt['summary_ticket']
            if ticket is None: #このifいらなくないか
                pass
            else:
                if ticket == '':
                    pass
                else:
                    return self.__validate_outline_b(ticket, t['name'],leaf_id)
        return None

    def __validate_outline(self, tkt, id):
        # tkt:InterTrac形式のチケット名
        # id:チケットのID
        # 戻り値:エラー文字列のリスト
        errors = []
        project_name = self.__get_project_name()
        t = self.__get_intertrac_ticket(tkt, False)
        error = t['error']
        if error is None:
            leaf_id = project_name + ':#' + str(id)
            e = self.__validate_outline_b(tkt, leaf_id, leaf_id)
            if e is None:
                pass
            else:
                errors.append((self.summary_label, e))
        return errors

    def __validate_ticket(self, ids, field_name, dep_en):
        # ids:カスタムフィールドに入っている値そのままです．
        # field_name: エラーを表示するためのフィールド名
        # dep_en: 親チケットを指定している場合はTrueになります．
        errors = []
        #リンクが正しいか確認します．
        if ids is None: #idになにも入ってない場合はエラーになるのでifが必要
            return errors
        if ids == '': #idになにも入ってない場合はエラーになるのでifが必要
            return errors
        # カンマで分割します．
        tickets = ids.split(',')
        for ticket in tickets: # 分割した文字列でループをまわります．
            # 一つ一つのチケットのリンクに問題がないか確認します．
            t = self.__get_intertrac_ticket(ticket, dep_en)
            error = t['error']
            if error: # エラーがなければ
                errors.append((field_name, error))
                continue
        return errors

    def validate_ticket_b(self, ticket):
        self.load_intertrac_setting()
        errors = []
        if self.config.get( TICKET_CUSTOM, "summary_ticket"): # カスタムフィールドが有効な場合
            # 親チケットが存在しているかとか指定方法に間違いがないかを確認する．
            label = self.config.get(TICKET_CUSTOM,"summary_ticket.label")
            errors.extend(self.__validate_ticket(ticket['summary_ticket'], label, False))
            # 親チケットがループしていないか確認する
            errors.extend(self.__validate_outline(ticket['summary_ticket'], ticket.id))
        if self.config.get( TICKET_CUSTOM, "dependencies"): # カスタムフィールドが有効な場合
            # 依存関係チケットが存在しているかとか指定方法に間違いがないかを確認する．
            label = self.config.get(TICKET_CUSTOM,"dependencies.label")
            errors.extend(self.__validate_ticket(ticket['dependencies'], label, True))
        return errors

    def __linkify_ids_p(self, ids, data):
        # チケットの表示のページでinterTracリンクの表示するための元を作る
        # 先行、親など指定しているidを検索する
        if ids is None:
            del data[-1]
        tickets = ids.split(',') #なにもない場合はエラーになるのでifが必要
        for ticket in tickets:
            t = self.__get_intertrac_ticket(ticket, True)
            error = t['error']
            if error is None:
                tkt = t['ticket']
                status = tkt['status']
                title1 = tkt['summary']
                data.append(tag.a(ticket, href=t['url'], class_='%s ticket'%status, title=title1))
                # 複数ある場合は", "を追加する
                data.append(', ')
        if data:
            # 最後のカンマを削除する．
            del data[-1]
        data.append(tag.br())

    def __linkify_ids_n(self, tickets2, data):
        # チケットの表示のページでinterTracリンクの表示するための元を作る
        for ticket in tickets2:
            tkt = ticket['ticket']
            url = ticket['url']
            status = ticket['status']
            title1 = ticket['title']
            data.append(tag.a('%s'%tkt, href=url, class_='%s ticket'%status, title=title1))
            data.append(', ')
        if data:
            # リストになにもない場合はラベル，ある場合は最後のカンマを削除する．
            del data[-1]

    def __get_info_tickets(self, ids):
        links = []
        if ids is None: #idになにも入ってない場合はエラーになるのでifが必要
            return links
        tickets = ids.split(',')
        for ticket in tickets:
            t = self.__get_intertrac_ticket(ticket, True)
            error = t['error']
            if error is None:
                tkt = t['ticket']
                status = tkt['status']
                title = tkt['summary']
                links.append({'ticket':ticket, 'title':title, 'url':t['url'], 'dep_url':t['url'], 'status':status})
            else:
                continue
        return links

    def get_dependency_info(self, tkt_id):
        # 依存関係表示ページ用のデータを作る
        self.load_intertrac_setting()
        tkt = Ticket(self.env, tkt_id)
        # チケットの情報から取得できる親チケットと依存関係のリンクを作る
        summary_ticket = self.__get_info_tickets(tkt['summary_ticket'])
        dependencies = self.__get_info_tickets(tkt['dependencies'])
        tkt_id_l = self.__get_project_name() + ':#' + tkt_id
        sub_ticket = self.__get_tickets_point_to(self.__get_subticket_other_prj(tkt_id_l), self.__get_subticket(tkt_id)) 
        subsequentticket = self.__get_tickets_point_to(self.__get_subsequentticket_other_prj(tkt_id_l), self.__get_subsequentticket(tkt_id)) 
        summary_ticket_enabled = not not ( self.config.get( TICKET_CUSTOM, "summary_ticket" ))
        dependencies_enabled = not not ( self.config.get( TICKET_CUSTOM, "dependencies"))
        custom_field = False
        return {'custom_field':custom_field,
                'summary_ticket': summary_ticket, 'dependencies': dependencies,
                'sub_ticket': sub_ticket, 'subsequentticket': subsequentticket,
                'summary_ticket_enabled': summary_ticket_enabled,
                'project_list_enabled': False,
                'dependencies_enabled':dependencies_enabled }

    def get_dependency_field_values(self, tkt):
        # post_process_requestから呼ばれる
        # 通常のチケット表示ページに使われる．
        self.load_intertrac_setting()
        tkt_id = str(tkt.id)
        tkt_id_l = self.__get_project_name() + ':#' + tkt_id
        sub_ticket = self.__get_tickets_point_to(self.__get_subticket_other_prj(tkt_id_l), self.__get_subticket(tkt_id)) 
        subsequentticket = self.__get_tickets_point_to(self.__get_subsequentticket_other_prj(tkt_id_l), self.__get_subsequentticket(tkt_id)) 
        
        data_summary = []
        data_depend = []
        
        data_summary.append(LABEL_SUMMARY)
        self.__linkify_ids_p(tkt['summary_ticket'], data_summary)
        data_summary.append(LABEL_SUB)
        self.__linkify_ids_n(sub_ticket, data_summary)
        
        data_depend.append(LABEL_PRECEDING)
        self.__linkify_ids_p(tkt['dependencies'], data_depend)
        data_depend.append(LABEL_SUBSEQUENT)
        self.__linkify_ids_n(subsequentticket, data_depend)
        
        return {'summary_ticket': tag.span(*data_summary), 'dependencies': tag.span(*data_depend)}

    def __get_project_name(self):
        return self.project_label

