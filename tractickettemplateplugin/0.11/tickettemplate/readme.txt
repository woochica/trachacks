= About this software =
 * http://trac-hacks.org/wiki/TracTicketTemplatePlugin
 * TicketTemplate is a Trac plugin. 
 * TicketTemplate enable users to create ticket using templates which can be customized by Trac administrator and themselves.
 * Trac administrator can spcify a general system level template '''default''' for all uncustomized ticket types.
 * System level ticket templates are ticket type specific.
 * User level ticket templates (ie, my template) can be managed by common users.
 * This version can work with Trac 0.11/0.12. 

= Changes in version 0.7 =
 * This version has fully i18n support with Trac 0.12dev r9098 above.
 * New feature: support '''My Template'''. Everyone can manage their own templates now.
 * New feature: template can include any fields, the default field is description.

= Install =

 '''IMPORTANT''': Please BACKUP you ticket templates if you are upgrading this plugin.

 You can install this software as normal Trac plugin.

 1. Uninstall TracTicketTemplate if you have installed before.

 2. Change to the directory containning setup.py.
 
 * (Optional): If you are using Trac 0.12 with i18n, you should compile language files here:
 {{{
python setup.py compile_catalog -f
}}} 

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

[tickettemplate]
field_list = summary, description, reporter, owner, priority, cc, milestone, component, version, type
}}}
 Set field_list to choose which field should be included in template.

= Usage =
 * Trac administrator should define the template for all ticket types:
  * Login as administrator, open Admin -> Ticket System -> Ticket Template
  * 'load' the template of each ticket type, modify them and 'apply changes'
 * After defined ticket template, normal user can create ticket using predefined template by change ticket types dropdown list items.