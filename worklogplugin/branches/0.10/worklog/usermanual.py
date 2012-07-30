user_manual_title = "Work Log Plugin User Manual"
user_manual_version = 2
user_manual_wiki_title = "WorkLogPluginUserManual"
user_manual_content = """
= !WorkLog Plugin User Manual =
This is a plugin that adds a Work Log capability to Trac.

Basically, it allows you to register the fact you have started work on a ticket which effectively allows you to clock on and clock off.

It uses javascript to add a button to the ticket page to allow you to start/stop working on a given ticket.

If the [http://trac-hacks.org/wiki/TimingAndEstimationPlugin TimingAndEstimationPlugin] is installed then when you clock off, the time spent on the ticket will be recorded.

If you visit the Work Log page (a new navigation entry), you will see a list of people (developers) and which tickets they are currently working on. Work log events are also logged to the Timeline for a historical view. 

In the future it will also provide an extension to the XMLRPC plugin which allows the integration with Desktop applications which will make interaction with this plugin seemless.
"""
