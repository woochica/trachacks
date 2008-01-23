= About this software =
 * http://trac-hacks.org/wiki/TicketTemplate(coming...)
 * TicketTemplate is a Trac plugin. 
 * TicketTemplate enable users to create ticket using templates which can be customized by Trac administrator.
 * Ticket templates are ticket type specific.
 * Trac administrator can spcify a general template '''default''' for all uncustomized ticket types.
 * This version tested with Trac 10.4. Other Trac versions may work too.

= Install =
 You can install this software as normal Trac plugin.
 * python setup.py install

= Prerequisite =
 * [http://trac-hacks.org/wiki/WebAdminPlugin WebAdminPlugin]

= Usage =
 * Trac administrator should define the template for all ticket types:
  * Login as administrator, open Admin -> Ticket System -> Ticket Template
  * 'load' the template of each ticket type, modify them and 'apply changes'
 * After defined ticket template, normal user can create ticket using predefined template by change ticket types dropdown list items.