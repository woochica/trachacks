= RelaTicket =

== Description ==
 * http://trac-hacks.org/wiki/RelaTicket
 * This software are helper scripts for [http://trac-hacks.org/wiki/RelaTicketAdmin RelaTicketAdmin] trac plugin.
 * RelaTicket are used to periodically generate keylist burndown statistic html files.

== Dependencies ==
 * [http://adodb.sourceforge.net Python Adodb]
 * [http://www.advsofteng.com ChartDirector for Python]

== Configuration ==
 1. Checkout or download these source files.

 2. Modify ''Settings'' in ini.py according to your environment.
 {{{
    'rootpath':'/path/to/the/parent/of/trac/environment'
    ,'projname':'TracProjectName'	# trac1
    ,'dbname':'db/trac.db'
    ,'ticketurl':'/url/of/trac/ticket'	# http://trac.abc.com/trac1/ticket
    ,'reporturl':'/url/of/trac/report'	# http://trac.abc.com/trac1/report
}}}

 3. Test: run below command, and you will get result html files in the directory 'exp'.
 {{{
python run_burndown.py
}}}

 4. If test passed, you should add above command to your crontab to make it run periodically.

== Download and Source ==

Check out [/svn/zoomquiettranslation/plugins/KSTracRelaTicket using Subversion], or [source:zoomquiettranslation/plugins/KSTracRelaTicket browse the source] with Trac.

== Recent Changes ==

[[ChangeLog(zoomquiettranslation/plugins/KSTracRelaTicket, 3)]]

== Author/Contributors ==

'''Author:''' [wiki:richard] [[BR]]
'''Contributors:'''