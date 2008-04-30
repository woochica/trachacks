= RelaTicket =

== 描述 ==
 * http://trac-hacks.org/wiki/RelaTicket
 * 该脚本是 [http://trac-hacks.org/wiki/RelaTicketAdmin RelaTicketAdmin] 的辅助脚本.
 * 用于定期生成关联传票视图HTML文件.

== 依赖 ==
 * [http://adodb.sourceforge.net Python Adodb]
 * [http://www.advsofteng.com ChartDirector for Python]

== 配置 ==
 1. 修改ini.py的''Settings''
 {{{
    'rootpath':'/path/to/the/parent/of/trac/environment'
    ,'projname':'TracProjectName'	# trac1
    ,'dbname':'db/trac.db'
    ,'ticketurl':'/url/of/trac/ticket'	# http://trac.abc.com/trac1/ticket
    ,'reporturl':'/url/of/trac/report'	# http://trac.abc.com/trac1/report
}}}

 2. 测试: 执行下面的命令, 在'exp'可以看到输出结果.
 {{{
python run_burndown.py
}}}

 3. 如果通过测试，需要将上述命令增加到crontab中.

== 下载 ==

 * [/svn/zoomquiettranslation/plugins/KSTracRelaTicket SVN]

 * [source:zoomquiettranslation/plugins/KSTracRelaTicket 浏览]
