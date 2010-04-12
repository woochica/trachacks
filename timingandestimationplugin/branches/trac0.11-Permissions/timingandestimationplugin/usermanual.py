user_manual_title = "Timing and Estimation Plugin User Manual"
user_manual_version = 14
user_manual_wiki_title = "TimingAndEstimationPluginUserManual"
user_manual_content = """

[[PageOutline]]
= Timing and Estimation Plugin User Manual =
[http://trac-hacks.org/wiki/TimingAndEstimationPlugin TimingAndEstimationPlugin on TracHacks] | [http://trac-hacks.org/report/9?COMPONENT=TimingAndEstimationPlugin Open Tickets] | [http://trac-hacks.org/newticket?component=TimingAndEstimationPlugin&owner=bobbysmith007 New Ticket]  | 
[http://trac-hacks.org/browser/timingandestimationplugin/trunk Web Browsable Source Code]

== Abstract Design Goal ==
My goal in writing this plugin was to use as much of the existing structure as possible (therefore not needing to add extra structure that might make maintainability difficult).  The largest downside I have found to this is that there is no way to attach more permissions to anything.

== Custom Ticket Fields ==
In adhering to our design goal, rather than creating a new ticket interface, I create some custom fields and a small daemon to watch over them.  

=== Fields: ===
 * '''Hours to Add''' This field functions as a time tracker.  When you add hours to it , those hours get added to the total hours field.  The person  who made the change is there fore credited with the hours spent on it.
 * '''Total Hours''' This field is the total number of hours that have been added to the project. This has been made uneditable by including javascript which replaces the input box with a span containing its value
   * Reports might not agree with each other if this is manually edited (which is possible if you disable javascript).
 * '''Is this billable?''' An extra flag on tickets so that they can be marked as billable / not billable.
 * '''Estimated Hours''' a field that contains the estimated amount of work
=== Future Fields ===
 * '''Ticket Rate''' The ability to attach a cost per hour or total amount to an individual ticket

== Billing / Management Page / Time Reports ==
This page provide a small interface for querying the tickets and adding a bill date at the current time.  
This interface mostly just gives you links that match the interface to open any of the give reports,
providing it the correct set of input parameters

The direct url is '/Billing'.

=== No Permissions Branch ===
The 'Management' button should be in the main title bar.  It is possible that if you are viewing at a low resolution, it was pushed off the edge of the screen.  Also if you are not logged in with report_view permissions, it will not show that button.

=== Permissions Branch ===
The 'Time Reports' button should be in the main title bar.  Whether or not you see this will be based on whether your user has TIME_VIEW permissions.




=== Set Bill Date ===

This button will add now as a bill date.  This is mostly to make it
easier to select the last time you billed.  This would allow you to
set a ticket as having been billed at a given time while others have
not, and accurately get the correct billing information for all
tickets.

== Reports ==
=== Report Types ===
We provide a few different reports for querying different types of data:
    * '''Billing Reports''' Currently the billing reports are the only time based reports, and are therefore useful for getting an estimate what tickets had times (and totals), and which developers spent their time where.
       * Ticket Work Summary
       * Milestone Work Summary
       * Developer Work Summary
    * '''Ticket/Hour Reports''' These reports are useful for reviewing estimates on a large scale or getting an idea of the project at large.  These reports currently ignore the time.
       * Ticket Hours
       * Ticket Hours with Description 
       * Ticket Hours Grouped By Component
       * Ticket Hours Grouped By Component with Description
       * Ticket Hours Grouped By Milestone
       * Ticket Hours Grouped By Milestone with Description
=== Adding More Reports ===
To add reports to the Management screen sections, you must run the following sql against your trac database
Remember to fill in the @reportID of the report you want to insert, and to select the insert statement for the section of your choice.
 * {{{INSERT INTO custom_report (id, uuid, maingroup, subgroup, version, ordering) VALUES (@reportID , @uuid, 'Timing and Estimation Plugin', 'Billing Reports', 1, 0);}}}
 * {{{INSERT INTO custom_report (id, uuid, maingroup, subgroup, version, ordering) VALUES (@reportID , @uuid, 'Timing and Estimation Plugin', 'Ticket/Hour Reports', 1, 0);}}}

''NB: @uuid is a globally uninque identifier created via a tool such as {{{uuidgen}}} on Linux or various [http://www.famkruithof.net/uuid/uuidgen online tools]. It is used in this plugin to provide programatic reference to specific reports such that they can be upgraded successfully on future revisions of the plugin''

=== Removing a Report ===
To remove reports from the Management page, run the following query. 
Remember to fill in the @reportID of the report you want to modify.
 * To remove for this version of the plugin (will be over written in future plugin upgrades)
   * {{{UPDATE custom_report SET maingroup='x'||maingroup WHERE report = @reportID;}}}
 * To remove permanently (wont be over written in future plugin upgrades)
   * {{{UPDATE custom_report SET version=9999, maingroup='x'||maingroup WHERE report = @reportID;}}}
''NB: The 'x' part is not important - you just need to make the column read something other than 'Timing and Estimation Plugin'.''

=== TAKE NOTE ===
 '''The reports can only be called from the Management Page. They will not work from the Trac View Tickets page. (Due to the custom variables that need values).'''

== Permissions Branch ==
Recently a branch of this plugin was sponsored by [http://www.obsidiansoft.com/ Obsidian Software] so that it would support per field permissions.  

This is accomplished with Genshi 5 stream filters in trac 11.  This code draws from the [http://trac-hacks.org/wiki/BlackMagicTicketTweaksPlugin BlackMagicTicketTweaksPlugin]
{{{
#!html
<br />
<a href="http://www.obsidiansoft.com/" >
<img src="http://trac-hacks.org/attachment/wiki/TimeEstimationUserManual/obsidian-logo.gif?format=raw" />
</a>
}}}

=== Configuration ===
There is a new trac.ini configuration section which is filled in by default as follows.
{{{
#!ini
[field settings] # per field permissions

# a list of all the fields to apply permissions to
fields = billable, totalhours, hours, estimatedhours, internal

# a bunch of:
# field.permission = PERMISSION:consequence
#
#  If PERMISSION=ALWAYS, then the consequence always occurs
#    eg: billable.permission = ALWAYS:hide 
#        will always result in billable being hidden, irrespective of user permissions    
#
# where consequence is one of: hide, remove, disable
#    hide - replaces with hidden input
#    remove - removes element
#    disable - removes input in favor of text
billable.permission = TIME_VIEW:hide, TIME_RECORD:disable
totalhours.permission = TIME_VIEW:remove, TIME_RECORD:disable
hours.permission = TIME_RECORD:remove
estimatedhours.permission = TIME_RECORD:disable
internal.permission = TIME_RECORD:hide
}}}

It also adds an "Internal" checkbox which allows you to set a ticket as internal.  For this policy to work correctly you need to add a line to the trac section of the config telling it which permission policies to use.  (The setup will attempt to put this line of configuration in place. )  The permission that looks at currently is 'TIME_ADMIN'.  To change that group set the internalgroup of the ticket section in the trac.ini as follows:

{{{
#!ini
[ticket]
internalgroup = TRAC_ADMIN #or whatever group / permission you want

[trac]
permission_policies = InternalTicketsPolicy, DefaultPermissionPolicy, LegacyAttachmentPolicy
}}}

== Future Improvements ==
 * [http://trac-hacks.org/report/9?COMPONENT=TimingAndEstimationPlugin See tickets] at the [http://trac-hacks.org/wiki/TimingAndEstimationPlugin project trac]

"""
