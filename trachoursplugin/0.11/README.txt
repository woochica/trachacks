= TracHoursPlugin = 

The goal of this plugin is to help keep trac of hours worked on
tickets.  This is done in response to
[http://trac-hacks.org/wiki/TimingAndEstimationPlugin TimingAndEstimationPlugin], but tailored to suit present needs:

 * Instead of adding hours via the comment system, there is a separate
  view for hours:

   - `/hours` is a management view.  This view displays the hours for all
   tickets for the last week (by default) in a way that combines the
   query interface for querying tickets and the timeline display for
   hours on the tickets in the time period.

   - query filters are available to find hours for people, hours for
   tickets of a certain component, etc;

   - a view for `/hours/<ticket number>`;  this displays the accrued hours
   for a particular ticket with a timeline-like view, but should also
   allow adding of new hours (by default, on "today", but this should
   be changeable via dropdown menus for day, month, year, etc),
   editing previously entered hours (amount, date, description) and
   deleting previously alloted hours

   - the view at `/hours/<ticket number>` by default will only display
   the hours on the ticket.  If you have the TICKET_ADD_HOURS
   permission, this view allows adding/editing
   of one's own hours on the ticket If you are a
   TRAC_ADMIN, you should be able to add/edit/delete others' hours as well

   - the default query period is the last seven days

 * Hours are uniquely assigned to tickets and people (required fields)

 * hours may have a description, which should be displayed in the
  applicable views;  if a description is provided, the hours and
  description are logged to ticket comments

 * `/ticket/<number>` has a link to `/hours/<number>` as the total
  hours field so that a user can add and view hours for the ticket

Hour tracking and estimation is most useful when the following questions can be answered:

 * How much time has been spent on a project?
 * How much time remains in a budget (estimate for a project)?
 * How much time have we committed to for the next time period ?
 * How much time is a developer committed to over the next time period?

If we put hour estimates on tickets, assign tickets to people, associate
tickets with milestones, and give milestones due dates, a good time
tracking plugin could generate reports to answer those questions.

For other trac time-tracking solutions, see
http://trac.edgewall.org/wiki/TimeTracking

== Multiproject Hours ==

The TracHoursPlugin exports RSS from the `/hours` handler.  This has
been utilized in consumption to provide hours reports across projects
sharing the same parent directory.  If {{{trachours.multiproject}}} is
enabled, then `/hours/multiproject` will become a handler front-ending
hours reports throughout the project and a link to this will appear on
the `/hours` page to `/hours/multiproject`.

The multiproject report breaks down hours by project and worker giving
row and column totals.  If there are no hours for a project then that
project will not be shown.
