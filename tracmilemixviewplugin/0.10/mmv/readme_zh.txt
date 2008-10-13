= MMV插件 =

== 描述 ==
 * http://trac-hacks.org/wiki/MMV
 * Trac里程综合视图, 统计里程碑的完成状况,并能显示父子关系的传票关系 

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
mmv.* = enabled

[mmv]
unplanned = [计划外]
ticket_custom_due = duetime
show_burndown_done = false
enable_unplanned = true
enable_relaticket = true
mmv_title = MMV
}}}

== 用法 ==
 * Trac管理员设置要生成视图的里程碑:
  * 作为管理员登录, 打开Admin -> Ticket System -> MMVTicket
  * 选择需要相应的里程碑

== 下载 ==

 * [/svn/zoomquiettranslation/plugins/KSTracMMV SVN]
 * [source:zoomquiettranslation/plugins/KSTracMMV 浏览]
