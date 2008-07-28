= 关于本软件 =
本软件包为Trac 0.11.x默认wiki页面的完整中文版本, 所有页面文件都位于default-pages目录中.

由于Trac 0.12开始支持国际化, 因此我们将重点放在了Trac 0.12版本的i18n支持上.

Trac 0.11先仅提供默认wiki页面的完整中文版本.

= 下载/更新 =
从trac-hacks.org下载/更新本软件包:
  {{{
svn co http://trac-hacks.org/svn/zoomquiettranslation/trunk/0.11.x
}}}

= 安装 =

 1. 安装默认wiki页面到项目环境中, 执行命令:
  {{{
trac-admin /path/to/your/env wiki load default-pages/
}}}

 2. 配置trac.ini, 增加如下配置:
  {{{
[mainnav]
wiki.href = /wiki/ZhWikiStart

[metanav]
help.href = /wiki/ZhTracGuide
}}}

 * 也可以不加mainnav配置, 使用默认的/wiki/WikiStart作为其实页.

 3. 复制ZhTracGuideToc.py到项目环境的plugins目录下.
