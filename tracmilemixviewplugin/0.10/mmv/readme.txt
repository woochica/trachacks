= About this software =
 * Trac MMV is a Trac plugin.

= Install =
 You can install this software as normal Trac plugin.

 1. Uninstall Trac MMV if you have installed before.

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
mmv.* = enabled

[mmv]
unplanned = [Unplanned]
ticket_custom_due = duetime
show_burndown_done = false
enable_unplanned = true
enable_relaticket = true
mmv_title = MMV

[ticket-custom]
duetime = text
duetime.label = duetime
duetime.value = 1d

}}}

= Prerequisite =
 * [http://trac-hacks.org/wiki/WebAdminPlugin WebAdminPlugin]

= Usage =
=== Trac administrators should setup which milstone to be displayed ===
  * Open Admin -> Ticket System -> MMVTicket
  * Select appropriate milstones

=== Create parent-child tickets ===
 1. Create parent ticket (eg, 1234) as normal, with empty duetime
 1. Create child tickets
  * Child tickets summary MUST start with {{{<#1234>}}}
  * Child tickets MUST set duetime value
