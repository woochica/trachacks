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

TICKET_CUSTOM = "ticket-custom"

class InterTrac:

    def __init__(self, config, env,project_label):
        # interTracの設定を取得します．
        self.intertracs0 = {}
        self.env = env
        self.summary_label = config.get(TICKET_CUSTOM,"summary_ticket.label")
        self.dependencies_label = config.get(TICKET_CUSTOM,"dependencies.label")
        for key, value in config.options('intertrac'):
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
        self.project_label = project_label

    def get_projects(self):
        return self.intertracs0

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

    def create_links(self, sql, sql_i, log):
        # InterTrac設定しているプロジェクトすべてを検索する必要がある,
        # 後続チケットまたは，子チケットへのリンクを作ります．
        links = []
        intertracs0 = self.get_projects()
        # すべてのinterTrc設定を回りサブチケットまたは後続チケットを探します．まずはInterTrac形式の指定のもの
        for prefix in intertracs0:
            intertrac = intertracs0[prefix]
            path = intertrac.get('path', '')
            try:
                project = open_environment(path, use_cache=True)
                db = project.get_db_cnx()
                cursor = db.cursor();
                cursor.execute(sql)
                for id, type, summary, owner, description, status in cursor:
                    url = intertrac.get('url', '') + '/ticket/' + str(id)
                    dep_url = intertrac.get('url', '') + '/dependency/ticket/' + str(id)
                    ticket = intertrac['name'] + ':#' + str(id)
                    links.append({'ticket':ticket, 'title':summary, 'url':url, 'dep_url':dep_url, 'status':status})
            except Exception, e:
                pass
            # オープンできない場合もあるのでエラー処理が必要
        try:
            # チケット番号のみの指定のサブチケットと後続チケットを探します．
            db = self.env.get_db_cnx()
            cursor = db.cursor();
            cursor.execute(sql_i)
            intertrac = intertracs0[self.get_project_name().lower()]
            for id, type, summary, owner, description, status in cursor:
                url = intertrac.get('url', '') + '/ticket/' + str(id)
                dep_url = intertrac.get('url', '') + '/dependency/ticket/' + str(id)
                ticket = self.get_project_name() + ':#' + str(id)
                links.append({'ticket':ticket, 'title':summary, 'url':url, 'dep_url':dep_url, 'status':status})
        except Exception, e:
            pass
        return links

    def create_ticket_links(self, tkt_id, log):
        tkt_id_l = self.get_project_name() + ':#' + tkt_id
        sub_ticket = self.create_links(self.subticket(tkt_id_l), self.subticket_i(tkt_id), log) 
        subsequentticket = self.create_links(self.subsequentticket(tkt_id_l), self.subsequentticket_i(tkt_id), log) 
        return sub_ticket, subsequentticket

    def linkify_ids_b(self, ids, label1, log):
        # チケットの表示のページでinterTracリンクの表示するための元を作る
        data = []
        if ids is None:
            return data
        tickets = ids.split(',') #なにもない場合はエラーになるのでifが必要
        data.append(label1)
        for ticket in tickets:
            t = self.get_ticket(ticket, self.get_project_name(), True, log)
            error = t['error']
            if error is None:
                tkt = t['ticket']
                status = tkt['status']
                title = tkt['summary']
                u = t['url']
                id = t['id']
                url = u + u'/ticket/' + id
                data.append(tag.a('%s'%ticket, href=url, class_='%s ticket'%tkt['status'], title=tkt['summary']))
                # 複数ある場合は", "を追加する
                data.append(', ')
        if data:
            # 最後のカンマを削除する．
            del data[-1]
        data.append(tag.br())
        return data

    def get_ticket(self, ticket, current_project_name, dep_en, log):
        # 指定されたInterTrac形式のチケット名から情報を取得する
        # 問題があった場合はエラーを返す．
        intertracs0 = self.intertracs0
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
                    return {'error':' project %s does not exist.'% project_name}
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
                        return {'error':'This field can not have dependency.'}
                    id, dep = id[:idx], id[idx+1:]
                    #依存関係に問題がないかの確認が必要
                    if dep.startswith('FF')==False and dep.startswith('FS')==False and dep.startswith('SF')==False and dep.startswith('SS')==False:
                        return {'error':'Unknown type of dependency.'}
                else:
                    dep = ''
                try:
                    # InterTracの設定のキーは小文字
                    intertrac = intertracs0[project_name.lower()]
                    path = intertrac.get('path', '')
                    project = open_environment(path, use_cache=True)
                    tkt = Ticket(project, id)
                    status = tkt['status']
                    title = tkt['summary']
                except Exception, e:
                    return {'error':'There is no ticket %s(%s,%s).'%(ticket, project_name, id)}
            else: #チケットに何も入っていない
                return {'error':'Many comma are in this field.'}
            return {'name':project_name+':#'+id, 'id':id, 'project':project, 'url':intertrac.get('url', ''), 'project_name':project_name, 'dependency':dep, 'error':None, 'ticket':tkt}
        else:
            return {'error': 'Ticekt 	not exists'}

    def validate_outline_b(self, ticket, sub_ticket, leaf_id, log):
        # tkt:InterTrac形式のチケット名
        # project_name:葉チケットのプロジェクト名
        # leaf_id:葉チケットのID
        # 戻り値:エラー文字列
        log.debug("validate_outline_b0010 ticket=%s, sub_ticket=%s, leaf_id=%s" , ticket, sub_ticket, leaf_id)
        error = []
        if ticket:
            ticket = ticket.strip() # 前後の空白を削除します
        if ticket == leaf_id:
            return 'Ticket(%s)\'s summary ticket is this ticket'%sub_ticket
        t = self.get_ticket(ticket, self.get_project_name(), False, log)
        error = t['error']
        if error is None:
            tkt = t['ticket']
            ticket = tkt['summary_ticket']
            if ticket is None:
                pass
            else:
                if ticket == '':
                    pass
                else:
                    return self.validate_outline_b(ticket, t['name'],leaf_id, log)
        return None

    def validate_outline(self, tkt, id, log):
        # tkt:InterTrac形式のチケット名
        # project_name:葉チケットのプロジェクト名
        # id:チケットのID
        # 戻り値:エラー文字列のリスト
        errors = []
        project_name = self.get_project_name()
        log.debug("validate_outline0010 project_name=%s tkt=%s id=%s" , project_name, tkt, id)
        t = self.get_ticket(tkt, self.get_project_name(), False, log)
        error = t['error']
        if error is None:
            leaf_id = project_name + u':#' + str(id)
            log.debug("validate_outline0020 leaf_id=%s" , leaf_id)
            e = self.validate_outline_b(tkt, leaf_id, leaf_id, log)
            if e is None:
                pass
            else:
                errors.append((self.summary_label, e))
        return errors

    def validate_ticket(self, ids, field_name, dep_en, log):
        # ids:カスタムフィールドに入っている値そのままです．
        # field_name: エラーを表示するためのフィールド名
        # dep_en: 親チケットを指定している場合はTrueになります．
        # log: ログを出力する先
        errors = []
        #リンクが正しいか確認します．
        if ids is None: #idになにも入ってない場合はエラーになるのでifが必要
            return errors
        if ids == '': #idになにも入ってない場合はエラーになるのでifが必要
            return errors
        # log.debug("test_link = %s" % ids)
        # カンマで分割します．
        tickets = ids.split(',')
        for ticket in tickets: # 分割した文字列でループをまわります．
            # 一つ一つのチケットのリンクに問題がないか確認します．
            t = self.get_ticket(ticket, self.get_project_name(), dep_en, log)
            error = t['error']
            if error: # エラーがなければ
                errors.append((field_name, error))
                continue
        return errors

    def linkify_ids(self, ids, label1, label2, tickets2, log):
        # チケットの表示のページでinterTracリンクの表示するための元を作る
        data = self.linkify_ids_b(ids, label1, log)
        data.append(label2)
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
        return tag.span(*data)

    def get_link(self, ids, log):
        links = []
        if ids is None: #idになにも入ってない場合はエラーになるのでifが必要
            return links
        tickets = ids.split(',')
        for ticket in tickets:
            t = self.get_ticket(ticket, self.get_project_name(), True, log)
            error = t['error']
            if error is None:
                tkt = t['ticket']
                status = tkt['status']
                title = tkt['summary']
                u = t['url']
                id = t['id']
                url = u + u'/ticket/' + id
                dep_url = u + '/dependency/ticket/' + id
                link = links.append({'ticket':ticket, 'title':title, 'url':url, 'dep_url':dep_url, 'status':status})
            else:
                continue
        return links

    def get_project_name(self):
        return self.project_label

