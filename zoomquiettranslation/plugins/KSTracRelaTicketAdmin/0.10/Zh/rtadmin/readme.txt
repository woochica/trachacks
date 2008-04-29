= RelaTicketAdmin Plugin =

== Description ==
 * http://trac-hacks.org/wiki/RelaTicketAdmin
 * RelaTicketAdmin is a Trac plugin. 
 * RelaTicketAdmin enable users to add/remove rela ticket by Trac Webadmin.

== Dependencies ==
 * [http://trac-hacks.org/wiki/WebAdminPlugin WebAdminPlugin]

== Configuration ==

 You can install this software as normal Trac plugin.

 1. Uninstall RelaTicketAdmin if you have installed before.

 2. Change to the directory containning setup.py.

 3. If you want to install this plugin globally, that will install this plugin to the python path:
  * python setup.py install

 4. If you want to install this plugin to trac instance only:
  * python setup.py bdist_egg
  * copy the generated egg file to the trac instance's plugin directory
  {{{
cp dist/*.egg /srv/trac/env/plugins
}}}

 5. Config trac.ini:
  {{{
[components]
rtadmin.* = enabled

[rtadmin]
base_path = /path/to/output/html/files    #/tracs/ctrl/keylist/KSTracRelaTicket/exp
}}}

== Usage ==
 * Trac administrator can specify which milestone should be handled by relaticket:
  * Login as administrator, open Admin -> Ticket System -> RelaTicket
  * 'check' milestones that will be handled by relaticket

== Download and Source ==

Check out [/svn/KSTracRelaTicketAdmin using Subversion], or [source:KSTracRelaTicketAdmin browse the source] with Trac.

== Recent Changes ==

[[ChangeLog(KSTracRelaTicketAdmin, 3)]]

== Author/Contributors ==

'''Author:''' [wiki:richard] [[BR]]
'''Contributors:'''