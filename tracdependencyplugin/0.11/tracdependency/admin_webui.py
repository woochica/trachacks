# -*- coding: utf-8 -*-

import re
import os.path

from genshi.builder import tag

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.admin import IAdminPanelProvider

from trac.env import open_environment

TICKET_CUSTOM = "ticket-custom"

ADMIN_PANEL_TRACDEP = u'Trac Dependency'
ADMIN_PANEL_INTERTRAC = "Inter Trac"
ADMIN_PANEL_CUSTOMFIELD = u'Custom Field'
ERROR_PROJECT_EXIST = 'Project already exists.'
ERROR_PROJECT_NOT_SEL = 'No intertrac setting selected'
LABEL_SUMMARY_TICKET = "Summary Ticket"
LABEL_DEPENDENCIES = "Dependencies"
LABEL_BASELINE_START = "Baseline start"
LABEL_BASELINE_FINISH = "Baseline finish"
LABEL_BASELINE_COST = "Baseline cost"

class TracDependencyAdminWebUI(Component):
    implements(IAdminPanelProvider, ITemplateProvider)

    def __init__(self):
        self.project_label = self.config.get( "tracdependency", "label")
        if not self.project_label:
            self.project_label=os.path.basename(self.env.path)
            # self.log.debug("base name of env_path = %s", self.project_label)
            intertrac_project_label = self.config.get( "intertrac", self.project_label+".label")
            if intertrac_project_label:
                self.project_label = intertrac_project_label
                # self.log.debug("label from intertrac setting = %s", self.project_label)

    def customfield_panel_enable(self):
        # カスタムフィールドパネルを有効にするかどうかの
        dependencies_enabled = ( self.config.get( TICKET_CUSTOM, "summary_ticket") or \
                     self.config.get( TICKET_CUSTOM, "dependencies"))
        baseline_enabled = ( self.config.get( TICKET_CUSTOM, "baseline_start") or \
                     self.config.get( TICKET_CUSTOM, "baseline_finish") or \
                     self.config.get( TICKET_CUSTOM, "baseline_cost"))
        return not(dependencies_enabled and baseline_enabled)

    # IAdminPanelProvider
    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            # 管理パネルに次の二つのメニューを追加します．
            # InterTrac設定の表示と設定を行うパネルを表示するメニューを追加します．
            yield ('Dependency', ADMIN_PANEL_TRACDEP, 'intertrac', ADMIN_PANEL_INTERTRAC)
            if self.customfield_panel_enable():
                # カスタムフィールドは追加しか準備していないため，必要が無ければ表示しません．
                yield ('Dependency', ADMIN_PANEL_TRACDEP, 'customfield', ADMIN_PANEL_CUSTOMFIELD)

    def project_information(self):
        # interTracの設定を取得します．
        intertracs0 = {}
        for key, value in self.config.options('intertrac'):
            # オプションの数のループを回り，左辺値の.を探します．
            idx = key.rfind('.')  
            if idx > 0: # .が無い場合はショートカットでので無視します
                prefix, attribute = key[:idx], key[idx+1:]  # 左辺値を分割します
                intertrac = intertracs0.setdefault(prefix, {})
                intertrac[attribute] = value    # 左辺値のピリオド以降をキーで右辺値を登録
                intertrac['name'] = prefix  # プロジェクト名を設定します．

        intertracs = []
        # 取得したinterTrac設定の名前が小文字になっているので元に戻します．
        # ついでに，プロジェクトの一覧表示用のデータを作成しておきます．
        # 結局はintertrac['label'] 設定することにしたので意味はないのですが，つくっちゃったのでこのままにします．
        for prefix in intertracs0:
            intertrac = intertracs0[prefix]
            # Trac.iniのパスを取得します
            path = intertrac.get('path', '')
            # trac.iniをオープンする
            project = open_environment(path, use_cache=True)
            # 名前をtrac.iniのプロジェクト名で置き換えます．
            intertrac['name'] = intertrac['label'] 
            # プロジェクトの一覧表示用のデータを作成します．
            url = intertrac.get('url', '')
            title = intertrac.get('title', url)
            name = project.project_name
            intertracs.append({'name': name, 'title': title, 'url': url, 'path': path})
        return intertracs

    def render_admin_panel(self, req, cat, page, path_info):
        custom_field = (page == 'customfield')
        if req.method == 'POST':
            if req.args.get('add'):
                # フォームに入力されたinterTracの設定を追加します．
                name = req.args.get('name')
                description = req.args.get('description')
                url = req.args.get('url')
                path = req.args.get('path')
                title = self.config.get('intertrac', name + '.title')
                if title: #プロジェクトがすでに存在していた場合はエラーにする．
                    raise TracError(ERROR_PROJECT_EXIST)
                self.config.set('intertrac', name + '.title', description)
                self.config.set('intertrac', name + '.url', url)
                self.config.set('intertrac', name + '.path', path)
                self.config.set('intertrac', name + '.label', name)
                self.config.save();
                req.redirect(req.href.admin(cat, page))

            elif req.args.get('remove'):
                # 選択されたinterTracの設定を削除します．
                sel = req.args.get('sel')
                if not sel:
                    raise TracError(ERROR_PROJECT_NOT_SEL)
                if not isinstance(sel, list):
                    sel = [sel]
                for name in sel:
                    self.config.remove('intertrac', name + '.title')
                    self.config.remove('intertrac', name + '.url')
                    self.config.remove('intertrac', name + '.path')
                    self.config.remove('intertrac', name + '.label')
                self.config.save();

            elif req.args.get('dependencies_create'):
                # 依存関係のカスタムフィールドを追加します
                self.config.set(TICKET_CUSTOM,"summary_ticket", "text")
                self.config.set(TICKET_CUSTOM,"summary_ticket.order", "50")
                self.config.set(TICKET_CUSTOM,"summary_ticket.label", LABEL_SUMMARY_TICKET)
                self.config.set(TICKET_CUSTOM,"dependencies", "text")
                self.config.set(TICKET_CUSTOM,"dependencies.order", "51")
                self.config.set(TICKET_CUSTOM,"dependencies.label", LABEL_DEPENDENCIES)
                self.config.save();

            elif req.args.get('baseline_create'):
                # 基準計画関連のカスタムフィールドを追加します．
                self.config.set(TICKET_CUSTOM,"baseline_start", "text")
                self.config.set(TICKET_CUSTOM,"baseline_start.order", "52")
                self.config.set(TICKET_CUSTOM,"baseline_start.label", LABEL_BASELINE_START)
                self.config.set(TICKET_CUSTOM,"baseline_finish", "text")
                self.config.set(TICKET_CUSTOM,"baseline_finish.order", "53")
                self.config.set(TICKET_CUSTOM,"baseline_finish.label", LABEL_BASELINE_FINISH)
                self.config.set(TICKET_CUSTOM,"baseline_cost", "text")
                self.config.set(TICKET_CUSTOM,"baseline_cost.order", "54")
                self.config.set(TICKET_CUSTOM,"baseline_cost.label", LABEL_BASELINE_COST)
                # TODO:なにも確認せずに追加しているだけなのでもう少しちゃんとする必要がある．
                # Trac-Hacksではここはコメントのほうがいい
                # calendar_fields = self.config.get( "decorator", "calendar_fields")
                # self.config.set("decorator", "calendar_fields", calendar_fields + ",baseline_start,baseline_finish")
                self.config.save();
        # 親チケットか依存関係のカスタムフィールドが存在したら
        dependencies_enabled = ( self.config.get( TICKET_CUSTOM, "summary_ticket") or \
                     self.config.get( TICKET_CUSTOM, "dependencies"))
        # 計画の開始と，計画の終了のどちらかがあったとき
        baseline_enabled = ( self.config.get( TICKET_CUSTOM, "baseline_start") or \
                     self.config.get( TICKET_CUSTOM, "baseline_finish"))

        intertracs = self.project_information()

        return 'admin_intertrac.html',{'intertracs': intertracs, 
                                       'dependencies_enabled': dependencies_enabled, 
                                       'baseline_enabled': baseline_enabled,
                                       'custom_field': custom_field}
    
    #ITemplateProvider
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('static', resource_filename('tracdependency', 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename('tracdependency', 'templates')]
