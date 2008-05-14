= MileMixViewAdmin插件 =

== 描述 ==
 * http://trac-hacks.org/wiki/MileMixViewAdmin
 * Trac关联传票视图统计里程碑的完成状况,并能显示父子关系的传票关系 

== 依赖 ==
 * [http://trac-hacks.org/wiki/WebAdminPlugin WebAdminPlugin]

== 配置 ==

 1. 请先卸载现有安装.

 2. 执行
  {{{
cp dist/*.egg /srv/trac/env/plugins
}}}

 3. 配置trac.ini:
  {{{
[components]
rtadmin.* = enabled

[rtadmin]
base_path = /path/to/output/html/files    #/tracs/ctrl/keylist/KSTracMileMixView
exp_path = exp
}}}

== 用法 ==
 * Trac管理员设置要生成视图的里程碑:
  * 作为管理员登录, 打开Admin -> Ticket System -> MileMixView
  * 选择需要相应的里程碑

== 下载 ==

 * [/svn/zoomquiettranslation/plugins/KSTracMileMixViewAdmin SVB]
 * [source:zoomquiettranslation/plugins/KSTracMileMixViewAdmin 浏览]
