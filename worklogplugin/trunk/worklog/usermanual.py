user_manual_title = "Work Log Plugin User Manual"
user_manual_version = 3
user_manual_wiki_title = "WorkLogPluginUserManual"
user_manual_content = """
= !WorkLog Plugin User Manual =
This is a plugin that adds a Work Log capability to Trac.

Basically, it allows you to register the fact you have started work on a ticket which effectively allows you to clock on and clock off.

== General stuff ==
The !WorkLog Plugin uses javascript to add a button to the ticket page to allow you to start/stop working on a given ticket.

If the [http://trac-hacks.org/wiki/TimingAndEstimationPlugin TimingAndEstimationPlugin] is installed then when you clock off, the time spent on the ticket will be recorded - but only if you explicitly enabled this on the [/admin/ticket/worklog plugins admin page].

If you visit the Work Log page (a new navigation entry), you will see a list of people (developers) and which tickets they are currently working on. Work log events are also logged to the Timeline for a historical view. 

In the future it will also provide an extension to the XMLRPC plugin which allows the integration with Desktop applications which will make interaction with this plugin seemless.

== Configuration ==
Configuration can be done on the plugins [/admin/ticket/worklog admin page] - or directly in the `trac.ini`. The following options are available:

||'''Option'''||'''`trac.ini`'''||'''description'''||
||Record time via Timing and Estimation Plugin?||timingandestimation = True|__False__||Whether to update the corresponding fields of the Timing and Estimation Plugin. By default, this is disabled. And of course, enabling this would require the [http://trac-hacks.org/wiki/TimingAndEstimationPlugin Timing and Estimation Plugin] to be installed and enabled.||
||Automatically add a comment when you stop work on a ticket?||comment = True|__False__||As it says: This will automatically add a comment even if you provide none.||
||Stop work automatically if ticket is closed?||autostop = True|__False__||Usually, you explicitly have to stop work on a ticket. But it's quite handy to do this automatically when closing the ticket (usually, you stop work then). But sometimes you just want to declare e.g. a bug fixed by closing the ticket, while stop working only after having documented your changes somewhere else - so it's up to you how it should be done.||
||Automatically reassign and accept (if necessary) when starting work?||autoreassignaccept = True|__False__||May ease the take-over of a ticket||
||Allow users to start working on a different ticket (i.e. automatically stop working on current ticket)?||autostopstart = True|__False__||If you switch to a new ticket, you usually stop working on the first one. So this saves you from doing so manually.||
||Round up to nearest minute||roundup = <n>||By default, time is rounded up to the full minute. If you want to round up to the next 15min interval, put a 15 here. To only have full hours logged, chose 60. But keep in mind, that a work of 1 minute will always be rounded up to the value defined here - so if rounding up to the full hour, a work of 1 minute will be recorded as 1 hour. Handy to increase your payment ;)||
"""
