= Trac报表管理 =

== 描述 ==
 * 保存报表
 * 从历史中恢复报表
 * 删除报表历史记录

== 安装 ==
 适用通用的Trac插件安装方法.

 1. 如果你已经安装过此插件的不同版本, 则请先卸载.

 2. 找到插件的setup.py.

 3. 如果你想进行全局安装, 该插件将安装到python的路径中:
 {{{
python setup.py install
}}}

 4. 如果你只安装到trac的实例中:
 {{{
python setup.py bdist_egg
cp dist/*.egg /srv/trac/env/plugins
}}}

 5. 配置trac.ini:
  {{{
[components]
reportmanager.* = enabled
}}}

== 下载 ==

 * [/svn/zoomquiettranslation/plugins/KSTracReportManager SVN]

 * [source:zoomquiettranslation/plugins/KSTracReportManager 浏览]
