= TracTweakUI插件 =

== 描述 ==
 * http://trac-hacks.org/wiki/TracTweakUI
 * 为使用javascript调节Trac的UI提供基础部署平台
 * 可在Trac的Web管理界面中, 定制每一个Trac调节的部分

== 配置 ==

 1. 请先卸载现有安装.

 2. 执行
  {{{
cp dist/*.egg /srv/trac/env/plugins
}}}

 3. 配置trac.ini:
  {{{
[components]
tractweakui.* = enabled
}}}

 4. 在Trac的环境的htdocs目录下, 创建下列目录结构:
  {{{
htdocs/tractweakui/
}}}

== 部署javascript插件editcc ==
 1. 在Trac环境目录下的htdocs/tractweakui/, 创建目录/文件结构如下:
   {{{
htdocs/tractweakui/editcc/__template__.js
htdocs/tractweakui/editcc/jquery.editcc.js
htdocs/tractweakui/editcc/jquery.editcc.css
htdocs/tractweakui/editcc/del.png
}}}
 1. 进入Trac的Web管理界面 -> TracTweakUI Admin
 1. 增加 路径(正则表达式): ^/newticket
 1. 进入路径 ^/newticket, 选择列出的filter
 1. 编辑filter的JS脚本, 并保存


== 下载 ==

 * [/svn/zoomquiettranslation/plugins/KSTracTweakUI SVN]
 * [source:zoomquiettranslation/plugins/KSTracTweakUI 浏览]