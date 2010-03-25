= About this software =
 * http://trac-hacks.org/wiki/TracTicketChainedFieldsPlugin
 * Trac Ticket Chained Fields is a Trac plugin.
 * Dynamicly change fields options by their parent fields

= Install =
 You can install this software as normal Trac plugin.

 1. Uninstall Trac Ticket Chained Fields if you have installed before.

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
tcf.* = enabled

[tcf]
hide_empty_fields = false
chained_fields = 
}}}

"hide_empty_fields" is the option which enable "hide fields when there are no supplied options", default is false. 

= Usage =
 * TBD