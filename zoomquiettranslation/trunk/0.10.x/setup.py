#!/usr/bin/env python
#coding:utf-8
import os
import os.path
import sys
import string
from glob import glob
from distutils.core import setup
from distutils.command.install import install
from distutils.command.install_data import install_data
from distutils.command.install_scripts import install_scripts
from stat import ST_MODE, S_ISDIR
import time

# 自己加入的,不改变trac本身的安装程序
seeAlso = {
'InterTrac':
[u'相关请见：[ZhTracLinks Trac链接处理], [ZhInterWiki 内部引用]',
'[[BR]]See also:TracLinks, InterWiki '],
'InterWiki':
[u'相关请见：[ZhInterTrac Trac内部引用], [ZhInterMapTxt 链接前缀表]',
'[[BR]]See also: InterTrac, InterMapTxt '],
'PageTemplates':
[u'相关请见：[ZhTracWiki 维基]',
'[[BR]]See also:TracWiki'],
'TracAccessibilit':
[u'相关信息：[ZhTracGuide 帮助]]',
'[[BR]]See also: TracGuide'],
'tracAdmin':
[u'相关信息：[ZhTracGuide 帮助], [ZhTracBackup 备份], [ZhTracPermissions 权限], [ZhTracEnvironment 环境], [ZhTracIni ini配置文件]',
'[[BR]]See also: TracGuide, TracBackup, TracPermissions'],
'TracBackup':
[u'相关信息：[ZhTracAdmin 管理], [ZhTracEnvironment 环境], [ZhTracGuide 帮助]',
'[[BR]]See also：TracAdmin, TracEnvironment, TracGuide'],

'TracBrowser':
[u'相关信息：[ZhTracGuide 帮助], [ZhTracChangeset 变更集]',
'[[BR]]See also: TracGuide, TracChangeset'],
'TracCgi':
[u'相关信息：[ZhTracGuide 帮助], [ZhTracInstall 安装], [ZhTracFastCgi FastCgi], [ZhTracModPython ModPython]',
'See also: TracGuide, TracInstall, TracFastCgi, TracModPython'],
'TracChangeset':
[u'相关信息：[ZhTracGuide 帮助], [ZhTracBrowser 代码浏览器]',
'See also: TracGuide, TracBrowser'],
'TracEnvironment':
[u'相关信息：[ZhTracAdmin 管理], [ZhTracBackup 备份], [ZhTracIni ini配置文件], [ZhTracGuide 帮助]',
'See also: TracAdmin, TracBackup, TracIni, TracGuide'],
'TracFastCgi':
[u'相关信息：[ZhTracCgi Cgi环境], [ZhTracModPython ModPython], [ZhTracInstall 安装], [ZhTracGuide 帮助]',
'See also: TracCgi, TracModPython, TracInstall, TracGuide'],
'TracGuide':
[u'相关信息：[ZhTracSupport Trac支持]',
'See also: TracSupport'],
'TracIni':
[u'相关信息：[ZhTracGuide 帮助], [ZhTracAdmin 管理], [ZhTracEnvironment 环境]',
'See also: TracGuide, TracAdmin, TracEnvironment'],
'TracInstall':
[u'相关信息： [ZhTracGuide 帮助], [ZhTracCgi Cgi环境], [ZhTracFastCgi FastCgi], [ZhTracModPython ModPython], [ZhTracUpgrade 升级], [ZhTracPermissions 权限]',
'See also: TracGuide, TracCgi, TracFastCgi, TracModPython, TracUpgrade, TracPermissions'],
'TracInterfaceCustomization':
[u'相关信息：[ZhTracGuide 帮助], [ZhTracIni ini配置文件]',
'See also: TracGuide, TracIni'],
'TracLinks':
[u'相关信息：[ZhWikiFormatting Wiki排板],[ ZhTracWiki 维基], [ZhWikiPageNames Wiki页面名], [ZhInterTrac Trac内部引用], [ZhInterWiki 内部引用]',
'See also: WikiFormatting, TracWiki, WikiPageNames, InterTrac, InterWiki'],
'TracLogging':
[u'相关信息：[ZhTracIni ini配置文件], [ZhTracGuide 帮助], [ZhTracEnvironment 环境]',
'See also: TracIni, TracGuide, TracEnvironment'],
'TracModPython':
[u'相关信息：[ZhTracGuide 帮助], [ZhTracInstall 安装], [ZhTracCgi Cgi环境], [ZhTracFastCgi FastCgi]',
'See also: TracGuide, TracInstall, TracCgi, TracFastCg'],
'TracNotification':
[u'相关信息：[ZhTracTickets 传票], [ZhTracIni ini配置文件], [ZhTracGuide 帮助]',
'See also: TracTickets, TracIni, TracGuide'],
'TracPermissions':
[u'相关信息：[ZhTracAdmin 管理], [ZhTracGuide 帮助 ]',
'See also: TracAdmin, TracGuide'],
'TracPlugins':
[u'相关信息：[ZhTracGuide 帮助], [http://trac.edgewall.org/wiki/PluginList plugin list], [http://trac.edgewall.org/wiki/TracDev/ComponentArchitecture 组件结构]',
'See also TracGuide, [http://trac.edgewall.org/wiki/PluginList plugin list], [http://trac.edgewall.org/wiki/TracDev/ComponentArchitecture component architecture]'],
'TracQuery':
[u'相关信息：[ZhTracTickets 传票], [ZhTracReports 报表], [ZhTracGuide 帮助]',
'See also: TracTickets, TracReports, TracGuide'],
'TracReports':
[u'相关信息：[ZhTracTickets 传票], [ZhTracQuery 查询], [ZhTracGuide 帮助]',
'See also: TracTickets, TracQuery, TracGuide'],
'TracRevisionLog':
[u'相关信息：[ZhTracBrowser 代码浏览器], [ZhTracChangeset 变更集], [ZhTracGuide 帮助]',
'See also: TracBrowser, TracChangeset, TracGuide'],
'TracRoadmap':
[u'相关信息：[ZhTracTickets 传票], [ZhTracReports 报表], [ZhTracQuery 查询], [ZhTracGuide 帮助]',
'See also: TracTickets, TracReports, TracQuery, TracGuide'],
'TracRss':
[u'相关信息：[ZhTracGuide 帮助], [ZhTracTimeline 时间轴], [ZhTracReports 报表], [ZhTracBrowser 代码浏览器]',
'See also: TracGuide, TracTimeline, TracReports, TracBrowser'],
'TracSearch':
[u'相关信息: [ZhTracGuide 帮助], [ZhTracLinks Trac链接处理], [ZhTracQuery 查询]',
'See also: TracGuide, TracLinks, TracQuery'],
'TracStandalone':
[u'相关信息: [ZhTracInstall 安装], [ZhTracCgi Cgi环境], [ZhTracModPython ModPython], [ZhTracGuide 帮助]',
'See also: TracInstall, TracCgi, TracModPython, TracGuide'],
'TracSupport':
[u'相关信息：[http://trac.edgewall.org/wiki/MailingList 邮件列表], [http://trac.edgewall.org/wiki/CommercialServices 社区]',
'See also: [http://trac.edgewall.org/wiki/MailingList MailingList], [http://trac.edgewall.org/wiki/CommercialServices CommercialServices]'],
'TracSyntaxColoring':
[u'相关信息：[ZhWikiProcessors 处理器], [ZhWikiFormatting Wiki排板], [ZhTracWiki 维基], [ZhTracBrowser 代码浏览器]',
'See slao: WikiProcessors, WikiFormatting, TracWiki, TracBrowser'],
'TracTickets':
[u'相关信息：[ZhTracGuide 帮助], [ZhTracWiki 维基], [ZhTracNotification 通知]',
'See also: TracGuide, TracWiki,  TracNotification'],
'TracTicketsCustomFields':
[u'相关信息： [ZhTracTickets 传票], [ZhTracIni ini配置文件]',
'See also: TracTickets, TracIni'],
'TracTimeline':
[u'相关信息：[ZhTracGuide 帮助], [ZhTracWiki 维基], [ZhWikiFormatting Wiki排板], [ZhTracRss Rss], [ZhTracNotification 通知]',
'See also: TracGuide, TracWiki, WikiFormatting, TracRss, TracNotification'],
'TracUpgrade':
[u'相关信息：[ZhTracGuide 帮助], [ZhTracInstall 安装]',
'See also: TracGuide, TracInstall'],
'TracWiki':
[u'相关信息：[ZhTracGuide 帮助]',
'See also: TracGuide'],
'WikiDeletePage':
[u'现关信息：[ZhTracWiki 维基], [ZhTracPermissions 权限]',
'See also: TracWiki, TracPermissions'],
'WikiFormatting':
[u'相关信息：[ZhTracLinks Trac链接处理], [ZhTracGuide 帮助], [ZhWikiHtml html格式], [ZhWikiMacros wiki宏], [ZhWikiProcessors 权限], [ZhTracSyntaxColoring 语法颜色]',
'See also: TracLinks, TracGuide, WikiHtml, WikiMacros, WikiProcessors, TracSyntaxColoring'],
'WikiHtml':
[u'相关信息：[ZhWikiProcessors 处理器],[ ZhWikiFormatting Wiki排板], [ZhWikiRestructuredText 重构文字]',
'See also: WikiProcessors, WikiFormatting, WikiRestructuredText'],
'WikiMacros':
[u'相关信息：[ZhWikiProcessors 处理器], [ZhWikiFormatting Wiki排板], [ZhTracGuide 帮助]',
'See also: WikiProcessors, WikiFormatting, TracGuide'],
'WikNewPage':
[u'相关信息：[ZhTracWiki 维基], [ZhWikiFormatting wiki排板], [ZhTracLinks Trac链接处理], [ZhWikiDeletePage 删除页面]',
'See also: TracWiki, WikiFormatting, TracLinks, WikiDeletePage'],
'WikiProcessors':
[u'相关信息：[ZhWikiMacros wiki宏], [ZhWikiHtml html格式], [ZhWikiRestructuredText 重构文字], [TZhracSyntaxColoring 语法颜色], [ZhWikiFormatting wiki排板], [ZhTracGuide 帮助]',
'See also: WikiMacros, WikiHtml, WikiRestructuredText, ZhTracSyntaxColoring, WikiFormatting, TracGuide'],
'WikiRestructuredText':
[u'相关信息：[ZhWikiRestructuredTextLinks 重构文字链接], [ZhWikiProcessors 处理器], [ZhWikiFormatting wiki排板]',
'See also: WikiRestructuredTextLinks, WikiProcessors, WikiFormatting'],
'WikiRestructuredTextLinks':
[u'相关信息：[ZhWikiRestructuredText 重构文字], [ZhTracLinks Trac链接处理]',
'See also: WikiRestructuredText, TracLinks']}


#测试权限函数
def testAccess(templateDir,tracDir):
    testList = [templateDir,
                tracDir + '/wiki',
                tracDir + '/versioncontrol',
                tracDir + '/ticket',]
    for test in testList:
        for (dirpath,dirs,files) in os.walk(test):
            for filename in files:
                fileDir = os.path.join(dirpath,filename)
                if os.access(fileDir,os.W_OK):
                    continue
                else:
                    # 退出for
                    assert 0
    testList = [tracDir + '/Settings.py',   
                tracDir + '/Search.py',
                tracDir + '/Timeline.py',
                tracDir + '/About.py',
                tracDir + '/web/auth.py',
                templateDir + '/../' + 'wiki-macros/TracGuideToc.py']
    for test in testList:
        if os.access(test,os.W_OK):
            continue
        else:
            assert 0

#汉化数据库的report表            
def tranReport(action):
    #定义字典
    ZhReport = {"""
 * List all active tickets by priority.
 * Color each row based on priority.
 * If a ticket has been accepted, a '*' is appended after the owner's name
""":u'''
 * 按优先级列出所有的活动传票
 * 颜色表示不同的优先级
 * 认领者认领的传票后,会有一个'*'加到的名字后面''',
"""
This report shows how to color results by priority,
while grouping results by version.

Last modification time, description and reporter are included as hidden fields
for useful RSS export.
""":u'''
本报表按版本分组,和按优先级列出不同颜色的结果.

当使用RSS阅读时,最后修改时间,描述与及创建人是被隐藏的'''
,
"""
This report shows how to color results by priority,
while grouping results by milestone.

Last modification time, description and reporter are included as hidden fields
for useful RSS export.
""":u'''
本报表按里程碑分组,和按优先级列出不同颜色的结果.

当使用RSS阅读时,最后修改时间,描述与及创建人是被隐藏的'''
,
"""
List assigned tickets, group by ticket owner, sorted by priority.
""":u'''
按传票认领者分组,按优先级排列''',
"""
List tickets assigned, group by ticket owner.
This report demonstrates the use of full-row display.
""":u'''
按创建者分组,列出已分配的活动传票,此报表使用全描述''',
"""
A more complex example to show how to make advanced reports.
""":u'''
复杂的查询例子,用于展示高级查询''',
"""
This report demonstrates the use of the automatically set 
USER dynamic variable, replaced with the username of the
logged in user when executed.
""":u'''
该报告展示了如何使用自动设置用户动态变量，将其替换为登录用户的用户名的方法。''',
"""
 * List all active tickets by priority.
 * Show all tickets owned by the logged in user in a group first.
""":u'''
 * 根据优先级别列举所有传票。
 * 先显示组内登录用户的所有传票。''',

}

    from trac.scripts import admin
    adminDb = admin.TracAdmin(sys.argv[2])
    if action == 'cn':
        for key , value in ZhReport.iteritems():
            adminDb.db_update('update report set description=%s where description=%s',params=(key,value))
        return
    elif action == 'en':
        for key , value in ZhReport.iteritems():
            adminDb.db_update('update report set description=%s where description=%s',params=(value,key))        
        return
                    
if sys.argv[1] in ('cn','en','upgrade'):
    # 要求trac实例的路径
    if len(sys.argv) < 3:
        print 'no environment file !'
        sys.exit(1)
    try:
        
        # 去掉当前目录,否则是可以import trac的
        sys.path.pop(0)
        # 使用这种方法判断系统是否已经安装trac
        import trac
        
# 增加版本判断
#        if :
#            pass
        import shutil
        import trac.siteconfig as siteconfig
        # py文件的目录
        tracDir = os.path.dirname(trac.__file__)
        # templates文件的目录
        templateDir = siteconfig.__default_templates_dir__
        # 这种方式比使用'.'安全
        curdir = os.path.dirname(__file__)
        backupdir = "%s/origin"%curdir
    except ImportError:
        print 'your computer has not install trac,install trac first please!'
        sys.exit()        
    ###
    
    if sys.argv[1] == 'cn':
        try:
            # 防止两次调用translate
            try:
                os.mkdir(backupdir)
            except OSError:
                print 'Error: exsit back up file,can not be second time translate trac'
                sys.exit()
            # 应该先测试权限
            print 'test Permission'
            testAccess(templateDir,tracDir)
            print 'Permission is OK'
            print 'copy template files '
            shutil.move(templateDir,backupdir + '/templates')
            print 'copy python code files'
            guideToc = os.path.abspath(templateDir +'/../wiki-macros')
            shutil.move(guideToc + '/TracGuideToc.py',backupdir + '/TracGuideToc.py')
            shutil.move(tracDir + '/wiki',backupdir + '/wiki')
            shutil.move(tracDir + '/versioncontrol',backupdir + '/versioncontrol')
            shutil.move(tracDir + '/ticket',backupdir + '/ticket')
            shutil.move(tracDir + '/Settings.py',backupdir + '/Settings.py')
            shutil.move(tracDir + '/Search.py',backupdir + '/Search.py')
            shutil.move(tracDir + '/Timeline.py',backupdir + '/Timeline.py')
            shutil.move(tracDir + '/About.py',backupdir + '/About.py')
            shutil.move(tracDir + '/web/auth.py',backupdir + '/auth.py')            
            print 'copy chinese template files'
            # 使用copytree,下次可以继续使用中文的templates
            shutil.copytree(curdir + '/templates',templateDir)
            print 'copy chinese python code files'
            shutil.copyfile(curdir + '/wiki-macros/TracGuideToc.py',templateDir + '/../wiki-macros/TracGuideToc.py')
            shutil.copyfile(curdir + '/wiki-macros/ZhTracGuideToc.py',templateDir + '/../wiki-macros/ZhTracGuideToc.py')
            shutil.copytree(curdir + '/trac/wiki', tracDir + '/wiki')
            shutil.copytree(curdir + '/trac/versioncontrol', tracDir + '/versioncontrol')
            shutil.copytree(curdir + '/trac/ticket', tracDir + '/ticket')
            shutil.copyfile(curdir + '/trac/Settings.py', tracDir + '/Settings.py')
            shutil.copyfile(curdir + '/trac/Search.py', tracDir + '/Search.py')
            shutil.copyfile(curdir + '/trac/Timeline.py', tracDir + '/Timeline.py')
            shutil.copyfile(curdir + '/trac/About.py', tracDir + '/About.py')
            shutil.copyfile(curdir + '/trac/web/auth.py', tracDir + '/web/auth.py')
            
            # 下面处理help页面
            import trac.scripts.admin as admin
            from trac.wiki.model import WikiPage
            from trac.env import Environment
            
            
            try:
                db_environ =os.path.abspath(sys.argv[2])
                print 'db path is %s' % db_environ
                myEnv = Environment(db_environ)
                myAdmin = admin.TracAdmin(db_environ)
                # 批量加入
                # 还没思考到同名wiki的情况
                myAdmin._do_wiki_load(curdir + '/zhwiki-default')
                print 'load chinese help finish'
            except :
                print 'can not import chinese help files '
                import traceback
                traceback.print_exc()
                sys.exit(1)                
            # 修改原英文帮助文件
            # 加入中文的帮助文件地址
            try:
                # 得到帮助文件名
                # 不应该使用wiki-default,应该使用zhwiki-default目录的listdir()
                # 因为有可以没有一些页面的中文版本
                help_zh = os.listdir(curdir + '/zhwiki-default')
                # \n 是后面安全去除添加内容的重要凭据
                headString = '\n\n[Zh%s 中文版本][[BR]]%s\n\n\n'
                headStringCN = '\n\n原文版本:%s[[BR]]%s\n\n\n'
                for docName in help_zh:
                    # 防止.svn目录
                    if not os.path.isdir(curdir + '/zhwiki-default/' + docName):
                        print 'editing %s' % docName
                        # 取英文文件名
                        doc = docName[2:]
                        # 英文文件
                        page = WikiPage(myEnv,doc)
                        if page.version == 0:
                            print '%s no exist!'
                            continue
                        seealso = seeAlso.get(doc,[''])
                        # %的两边要达到统一编码
                        addString = headString % (doc,seealso[0].encode('utf8'))
                        addString = addString.decode('utf8')
                        page.text = addString + page.text
                        page.save('Trac','','')
                        # 中文文件
                        page = WikiPage(myEnv,docName)
                        if page.version == 0:
                            print '%s no exist!'
                            continue
                        seealso = seeAlso.get(doc,[''])
                        # %的两边要达到统一编码
                        seealso[0] = seealso[0].encode('utf8')
                        seealsoStr = '[[BR]]'.join(seealso)
                        addString = headStringCN % (doc,seealsoStr)
                        addString = addString.decode('utf8')
                        page.text = addString + page.text
                        page.save('Trac','','')                        
                print 'add chinese help link to english help successful'
            except :
                import traceback
                print 'Error: can not edit english help files'
                traceback.print_exc()
                sys.exit(1)
            # 汉化数据库数据
            tranReport('cn')
            # 要退出,否则调用trac本身的安装程序代码
            print 'install is finish successful '
            sys.exit()
        except (OSError,AssertionError),error:
            if type(error) == AssertionError:
                print 'Error: Are you sure you have root power to do this?'
            # 一次性删除所有复制的文件
            shutil.rmtree(backupdir)
            sys.exit(1)
    elif sys.argv[1] == 'en':
        try:
            # 应该先测试权限
            print 'test Permission'
            testAccess(templateDir,tracDir) 
            print 'Permission is OK'    
            shutil.rmtree(templateDir)
            shutil.move(backupdir + '/templates',templateDir)
            shutil.rmtree(tracDir + '/wiki')
            shutil.move(backupdir + '/wiki',tracDir + '/wiki')
            shutil.rmtree(tracDir + '/versioncontrol')
            shutil.move(backupdir + '/versioncontrol', tracDir + '/versioncontrol')
            shutil.rmtree(tracDir + '/ticket')
            shutil.move(backupdir + '/ticket', tracDir + '/ticket')
            shutil.move(backupdir + '/Settings.py', tracDir + '/Settings.py')
            shutil.move(backupdir + '/Search.py', tracDir + '/Search.py')
            shutil.move(backupdir + '/Timeline.py', tracDir + '/Timeline.py')
            shutil.move(backupdir + '/About.py', tracDir + '/About.py')
            shutil.move(backupdir + '/auth.py', tracDir + '/web/auth.py')
            shutil.move(backupdir + '/TracGuideToc.py', templateDir + '/../wiki-macros/TracGuideToc.py')        
            
            
            # 把中文帮助文件删除
            # 把英文版本的中文链接去掉
            try:
                import trac.scripts.admin as admin
                from trac.wiki.model import WikiPage
                from trac.env import Environment     
                           
                db_environ =os.path.abspath(sys.argv[2])
                print 'db path is %s' % db_environ
                myEnv = Environment(db_environ)
                myAdmin = admin.TracAdmin(db_environ)
                # 中文帮助文件名
                help_zh = os.listdir(curdir + '/zhwiki-default')
                for filename in help_zh:
                    # 防止一个.svn目录抛异常
                    if not os.path.isdir(filename):
                        try:
                            myAdmin._do_wiki_remove(filename)
                        except AssertionError:
                            continue
                        # 下面去掉中文链接
                        page = WikiPage(myEnv,filename[2:])
                        if page.version == 0:
                            continue
                        txt = page.text
                        start = txt.index('\n\n')
                        end = txt.index('\n\n\n')
                        txt = txt[0:start] + txt[end + 3:]
                        #txt = txt.replace(u'\n\n[%s 中文版本]\n\n\n'%filename,u'')
                        page.text = txt
                        page.save('trac','','')
                
            except :
                import traceback
                traceback.print_exc()
                sys.exit(1)
                                
            shutil.rmtree(backupdir)
            # 返回被汉化的数据库数据
            tranReport('en')            
            print 'install is finish successful '
        except OSError:
            print 'Error: Are you sure you have root power to do this?'
            sys.exit()
        #  要退出,否则调用trac本身的安装程序代码
        sys.exit()
    elif sys.argv[1] == 'upgrade':
        # 把中文帮助文件删除
        try:
            import trac.scripts.admin as admin
            from trac.wiki.model import WikiPage
            from trac.env import Environment     
                       
            db_environ =os.path.abspath(sys.argv[2])
            print 'db path is %s' % db_environ
            myEnv = Environment(db_environ)
            myAdmin = admin.TracAdmin(db_environ)
            # 中文帮助文件名
            help_zh = os.listdir(curdir + '/zhwiki-default')

            # 保存被用户修改的wiki文章
            # 存放要加新版本wiki链接的文章
            ChangedWiki = []
            for filename in help_zh:
                # 防止一个.svn目录抛异常
                if not os.path.isdir(filename):
                    try:
                        # 删除前要判断用户是否修改过
                        # 修改过就保留
                        dbase = myAdmin.db_query('select max(version),text from wiki where name = %s',params=(filename,))
                        try:
                            col = dbase.next()
                            print 'version is %s'%col[0]
                            if col[0] > 2:
                                # 要加新版本wiki链接的文章
                                ChangedWiki.append([col[0],col[1],filename])
                                continue
                        except  Exception, e:
                            # 没有些文件
                            print 'no file %s '%filename
                            continue
                        # version == 1的文章都要删除
                        print 'remove %s '%filename
                        dbase.close()
                        myAdmin._do_wiki_remove(filename)
                    except AssertionError:
                        print 'error'
                        continue
            # 加入新版本的中文帮助文件
            # 如果有同名的wiki文章,就只增加一个链接
            DoNotImport = []
            for member in ChangedWiki:
                DoNotImport.append(member[2])
                member[1] = member[1] + (u'\n\n[[BR]][wiki:%s 最新汉化wiki%s]\n\n' % (member[2]+str(member[0]),member[0]))
                # 版本号增加1
                # 增加wiki文章链接
                myAdmin.db_update("INSERT INTO wiki(version,name,time,author,ipnr,text) "
                       " SELECT 1+COALESCE(max(version),0),%s,%s,"
                       " 'trac','127.0.0.1',%s FROM wiki "
                       " WHERE name=%s",
                       None, (member[2], int(time.time()), member[1], member[2]))              
                # 增加新版本的wiki文章
                WikiFile = open(curdir + '/zhwiki-default/' + member[2])
                NewWikiDate = WikiFile.read()
                WikiFile.close()
                myAdmin.db_update("INSERT INTO wiki(version,name,time,author,ipnr,text) "
                       " SELECT 1+COALESCE(max(version),0),%s,%s,"
                       " 'trac','127.0.0.1',%s FROM wiki "
                       " WHERE name=%s",
                       None, (member[2]+str(member[0]), int(time.time()), NewWikiDate, member[2]+str(member[0])))
            print 'changed wiki %s'%str(DoNotImport)
            myAdmin._do_wiki_load(curdir + '/zhwiki-default', ignore=DoNotImport)
            
            
            
            # 汉化数据库数据
            tranReport('cn')
            sys.exit()
        except Exception,e:
            if e != SystemExit:
                import traceback
                traceback.print_exc()
                sys.exit()
        


# 程序原代码
import trac

PACKAGE = 'Trac'
VERSION = str(trac.__version__)
URL = trac.__url__
LICENSE = trac.__license__

if sys.version_info < (2, 3):
    print >>sys.stderr, 'You need at least Python 2.3 for %s %s' \
                        % (PACKAGE, VERSION)
    sys.exit(3)

def _p(unix_path):
     return os.path.normpath(unix_path)

class my_install (install):
     def run (self):
         self.siteconfig()

     def siteconfig(self):
         path = self.prefix or self.home
         path = os.path.expanduser(path)
         conf_dir = os.path.join(path, 'share', 'trac', 'conf')
         templates_dir = os.path.join(path, 'share', 'trac', 'templates')
         htdocs_dir = os.path.join(path, 'share', 'trac', 'htdocs')
         wiki_dir = os.path.join(path, 'share', 'trac', 'wiki-default')
         macros_dir = os.path.join(path, 'share', 'trac', 'wiki-macros')
         plugins_dir = os.path.join(path, 'share', 'trac', 'plugins')
         f = open(_p('trac/siteconfig.py'), 'w')
         f.write("""
# PLEASE DO NOT EDIT THIS FILE!
# This file was autogenerated when installing %(trac)s %(ver)s.
#
__default_conf_dir__ = %(conf)r
__default_templates_dir__ = %(templates)r
__default_htdocs_dir__ = %(htdocs)r
__default_wiki_dir__ = %(wiki)r
__default_macros_dir__ = %(macros)r
__default_plugins_dir__ = %(plugins)r

""" % {'trac': PACKAGE, 'ver': VERSION, 'conf': _p(conf_dir),
       'templates': _p(templates_dir), 'htdocs': _p(htdocs_dir),
       'wiki': _p(wiki_dir), 'macros': _p(macros_dir),
       'plugins': _p(plugins_dir)})
         f.close()

         # Run actual install
         install.run(self)
         print
         print "Thank you for choosing Trac %s. Enjoy your stay!" % VERSION
         print

class my_install_scripts (install_scripts):
    def initialize_options (self):
        install_scripts.initialize_options(self)
        self.install_data = None
        
    def finalize_options (self):
        install_scripts.finalize_options(self)
        self.set_undefined_options('install',
                                   ('install_data', 'install_data'))
          
    def run (self):
        if not self.skip_build:
            self.run_command('build_scripts')

        self.outfiles = []

        self.mkpath(os.path.normpath(self.install_dir))
        ofile, copied = self.copy_file(os.path.join(self.build_dir,
                                                     'trac-admin'),
                                        self.install_dir)
        if copied:
            self.outfiles.append(ofile)
        ofile, copied = self.copy_file(os.path.join(self.build_dir,
                                                     'tracd'),
                                        self.install_dir)
        if copied:
            self.outfiles.append(ofile)
            
        cgi_dir = os.path.join(self.install_data, 'share', 'trac', 'cgi-bin')
        if not os.path.exists(cgi_dir):
            os.makedirs(cgi_dir)
            
        ofile, copied = self.copy_file(os.path.join(self.build_dir,
                                                    'trac.cgi'), cgi_dir)
        if copied:
            self.outfiles.append(ofile)

        ofile, copied = self.copy_file(os.path.join(self.build_dir,
                                                    'trac.fcgi'), cgi_dir)
        if copied:
            self.outfiles.append(ofile)
         
        for path in ('plugins', 'conf'):
            full_path = os.path.join(self.install_data, 'share', 'trac', path)
            if not os.path.exists(full_path):
                os.makedirs(full_path)
            
        if os.name == 'posix':
            # Set the executable bits (owner, group, and world) on
            # all the scripts we just installed.
            for file in self.get_outputs():
                if not self.dry_run:
                    mode = ((os.stat(file)[ST_MODE]) | 0555) & 07777
                    os.chmod(file, mode)
        elif os.name == 'nt':
            # Install post-install script on windows
            ofile, copied = self.copy_file(os.path.join(self.build_dir,
                                                        'trac-postinstall.py'),
                                            self.install_dir)
            if copied:
                self.outfiles.append(ofile)


class my_install_data (install_data):
    def run (self):
        install_data.run(self)

        if os.name == 'posix' and not self.dry_run:
            # Make the data files we just installed world-readable,
            # and the directories world-executable as well.
            for path in self.get_outputs():
                mode = os.stat(path)[ST_MODE]
                if S_ISDIR(mode):
                    mode |= 011
                mode |= 044
                os.chmod(path, mode)

# Our custom bdist_wininst
import distutils.command.bdist_wininst
from distutils.command.bdist_wininst import bdist_wininst
class my_bdist_wininst(bdist_wininst):
    def initialize_options(self):
        bdist_wininst.initialize_options(self)
        self.title = 'Trac %s' % VERSION
        self.bitmap = 'setup_wininst.bmp'
        self.install_script = 'trac-postinstall.py'
distutils.command.bdist_wininst.bdist_wininst = my_bdist_wininst


# parameters for various rpm distributions
rpm_distros = {
    'suse_options': { 'version_suffix': 'SuSE',
                      'requires': """python >= 2.3
                        subversion >= 1.0.0
                        pysqlite >= 0.4.3
                        clearsilver >= 0.9.3
                        httpd""" },

    'fedora_options': { 'version_suffix': 'fc'}
    }


# Our custom bdist_rpm
import distutils.command.bdist_rpm
from distutils.command.bdist_rpm import bdist_rpm
class generic_bdist_rpm(bdist_rpm):

    def __init__(self, dist, distro):
        self.distro = distro
        bdist_rpm.__init__(self, dist)

    def initialize_options(self):
        bdist_rpm.initialize_options(self)
        self.title = "Trac %s" % VERSION
        self.packager = "Edgewall Software <info@edgewall.com>"
        for x in rpm_distros[self.distro].keys():
            setattr(self, x, rpm_distros[self.distro][x])
        self.install_script = "scripts/rpm-install.sh"

    def run(self):
        bdist_rpm.run(self)
        if hasattr(self, 'version_suffix'):
            prefix = os.path.join(self.dist_dir, string.lower(PACKAGE)+'-'+VERSION+'-1')
            os.rename(prefix+'.noarch.rpm', prefix+self.version_suffix+'.noarch.rpm')
            os.rename(prefix+'.src.rpm', prefix+self.version_suffix+'.src.rpm')

class proxy_bdist_rpm(bdist_rpm):

    def __init__(self, dist):
        bdist_rpm.__init__(self, dist)
        self.dist = dist

    def initialize_options(self):
        bdist_rpm.initialize_options(self)

    def run(self):
        for distro in rpm_distros.keys():
            r = generic_bdist_rpm(self.dist, distro)
            r.initialize_options()
            self.dist._set_command_options(r, self.dist.command_options['bdist_rpm'])
            r.finalize_options()
            r.run()

distutils.command.bdist_rpm.bdist_rpm = proxy_bdist_rpm

setup(name="trac",
      description="Integrated scm, wiki, issue tracker and project environment",
      long_description=\
"""
Trac is a minimalistic web-based software project management and bug/issue
tracking system. It provides an interface to the Subversion revision control
systems, an integrated wiki, flexible issue tracking and convenient report
facilities.
""",
      version=VERSION,
      author="Edgewall Software",
      author_email="info@edgewall.com",
      license=LICENSE,
      url=URL,
      packages=['trac', 'trac.db', 'trac.mimeview', 'trac.scripts',
                'trac.ticket', 'trac.upgrades', 'trac.util', 'trac.web',
                'trac.versioncontrol', 'trac.versioncontrol.web_ui', 
                'trac.wiki'],
      data_files=[(_p('share/trac/templates'), glob('templates/*')),
                  (_p('share/trac/htdocs'), glob(_p('htdocs/*.*')) + [_p('htdocs/README')]),
                  (_p('share/trac/htdocs/css'), glob(_p('htdocs/css/*'))),
                  (_p('share/trac/htdocs/js'), glob(_p('htdocs/js/*'))),
                  (_p('share/man/man1'), glob(_p('scripts/*.1'))),
                  (_p('share/trac/wiki-default'), glob(_p('wiki-default/[A-Z]*'))),
                  (_p('share/trac/zhwiki-default'), glob(_p('zhwiki-default/[Zh]*'))),   #中文帮助文件
                  (_p('share/trac/wiki-macros'), glob(_p('wiki-macros/*.py')))],
      scripts=[_p('scripts/trac-admin'),
               _p('scripts/trac-postinstall.py'),
               _p('scripts/tracd'),
               _p('cgi-bin/trac.cgi'),
               _p('cgi-bin/trac.fcgi')],
      cmdclass = {'install': my_install,
                  'install_scripts': my_install_scripts,
                  'install_data': my_install_data})
