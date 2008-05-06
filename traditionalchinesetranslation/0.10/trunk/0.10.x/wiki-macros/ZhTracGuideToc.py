# -*- coding: utf-8 -*-
"""
This macro shows a quick and dirty way to make a table-of-contents for a set
of wiki pages.
"""

Zh_TOC = [('ZhTracGuide',                    u'索引'),
       ('ZhTracInstall',                  u'安裝'),
       ('ZhTracUpgrade',                  u'升級'),
       ('ZhTracIni',                      u'配置'),
       ('ZhTracAdmin',                    u'管理'),
       ('ZhTracBackup',                   u'恢復'),
       ('ZhTracLogging',                  u'日誌'),
       ('ZhTracPermissions' ,             u'權限'),
       ('ZhTracWiki',                     u'Wiki幫助'),
       ('ZhWikiFormatting',               u'Wiki格式'),
       ('ZhTracTimeline',                 u'時間軸'),
       ('ZhTracBrowser',                  u'代碼庫'),
       ('ZhTracChangeset',                u'變量集'),
       ('ZhTracRoadmap',                  u'路線圖'),
       ('ZhTracTickets',                  u'傳票'),
       ('ZhTracQuery',                    u'傳票查詢'),
       ('ZhTracReports',                  u'報表'),
       ('ZhTracRss',                      u'RSS支持'),
       ('ZhTracNotification',             u'通知'),
       ('ZhTracInterfaceCustomization',   u'自定義'),
       ('ZhTracPlugins',                  u'插件'),
       ('ZhAbout',                        u'關於漢化版Trac')
       ]



def execute(hdf, args, env):
    html = u'<div class="wiki-toc">' \
           '<h4>Contents</h4>' \
           '<ul>'
    curpage = '%s' % hdf.getValue('wiki.page_name', '')
    lang, page = '/' in curpage and curpage.split('/', 1) or ('', curpage)
    for (ref, title) in Zh_TOC:
        if page == ref:
            cls =  ' class="active"'
        else:
            cls = ''
        html += '<li%s><a href="%s">%s</a></li>' \
                % (cls, env.href.wiki(lang+ref), title)
    return html + '</ul></div>'
