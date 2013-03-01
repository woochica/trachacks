An example usage::

You can see here how to use this macro:

   {{{
   #!div class=blogflash
   [[UpcomingMilestonesChart(%-%,10,Next Milestone Dates,yellow)]]
   }}}

The example sets
 * an SQL filter pattern {{{ %-% }}} means here only to display milestones containing a minus in the middle of the name
 * a maximum of 10 milestones  
 * a title
 * the color of overdue milestones, leave it out and just set the comma for no color
 * and puts it in a news box
