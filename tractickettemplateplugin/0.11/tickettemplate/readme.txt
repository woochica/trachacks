= About this software =
 * http://trac-hacks.org/wiki/TicketTemplate(coming...)
 * TicketTemplate is a Trac plugin. 
 * TicketTemplate enable users to create ticket using templates which can be customized by Trac administrator.
 * Ticket templates are ticket type specific.
 * Trac administrator can spcify a general template '''default''' for all uncustomized ticket types.
 * This version tested with Trac 10.4. Other Trac versions may work too.

= Install =

 '''IMPORTANT''': Please BACKUP you ticket templates if you are upgrading this plugin.

 You can install this software as normal Trac plugin.

 1. Uninstall TracTicketTemplate if you have installed before.

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
tickettemplate.* = enabled
}}}

 6. If you are installing this plugin first time, you can copy description.tmpl to your/trac/environment/templates to utilize some default ticket templates.

= Prerequisite =
 * [http://trac-hacks.org/wiki/WebAdminPlugin WebAdminPlugin]

= Usage =
 * Trac administrator should define the template for all ticket types:
  * Login as administrator, open Admin -> Ticket System -> Ticket Template
  * 'load' the template of each ticket type, modify them and 'apply changes'
 * After defined ticket template, normal user can create ticket using predefined template by change ticket types dropdown list items.