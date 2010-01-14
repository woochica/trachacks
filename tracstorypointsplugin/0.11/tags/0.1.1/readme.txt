This plug-in aims to provide some very simple support for story point 
estimation and tracking.

This plugin adds the following fields to Trac Tickets by adding them to 
the trac.ini file for the site. 

ADDITIONAL TICKET FIELDS 

Storypoints - Dropdown field listing story point values.  The values used
              can be customized in the sites trac.ini file if needed.
              field name: storypoints
              
Date Completed - A text field to enter the date a ticked is completed.
                 Format must be mm/dd/YYYY.  See notes below for adding
                 a plugin for a calander widget to this field.
                 fieldname: completed
                 
User Story - A text field to enter in a keyword to associate this with a
             particular user story.
             fieldname: userstory
             
CHANGES TO TRAC REPORTS

This plugin deactivates the legacy trac reports system in favor of the new
ticket query system.  This allows custom querying of tickets and ticket fields
so the additional ticket fields can be easily displayed.

See http://trac.edgewall.org/wiki/TracReports for more Information on 
Trac Reports versus Trac Query module.

IMPROVED TRAC TICKET QUERY WIKI MACROS

This plugin provides improved Trac Ticket Query Wiki Macros as well as additional
formats for the query.   It it important to understand this behaves just like 
normal Track Ticket Queries with some additional options.

For More information o Trac Ticket Query Wiki Macros see 
http://trac.edgewall.org/wiki/TracQuery

To use the expanded TICKET QUERY macros use SpTicketQuery instead of TickeyQuery

ADDITIONAL FEATURES OF SpTicketQuery

In standard TicketQuery macros you can add additional column to table format by 
specifying a col attribute.  This plugin extends that to list format as well,
appending additional fields as annotations at the end of the summary.

For example:
[[SpTicketQuery(milestone=User Dashboard, format=list,col=id|summary|storypoints|completed)]]

SpTicketQuery also provides several new formats for the ticket query, related to
story point reporting.

These additional formats are:

* format=total - Returns the total story points for all tickets in the query.

* format=completed - Returns the total story points of all closed tickets in a query.

* format=remaining - Returns the total story points of all non-closed tickets in a query.

* format=storypoints - Returns a string summarizing total, completed and remaining story
                       points for all tickets in a query.
                       example: 16.0 Total Story Points with 13.0 Completed and 3.0 Remaining.

INSTALLATION

Trac plugins are installed as python eggs and this plugin requires no special 
installation. See http://trac.edgewall.org/wiki/TracPlugins for more
information.

In a nutshell just upload and activate the python egg via your trac sites 
admin > plugins page.  Alternatively running easy_install on the egg file 
to install the plugin and make it available for all sites in a trac multi-
site installation.

If you are installing from source just checkout the source and run 
'python setup.py bdist_egg' to create an egg file.  You can locate the 
resulting egg file from the output of the bdist buffer.

UNINSTALLING

Decativate the plugin in the admin section for your individual site.  Then modify
site site trac.ini file to remove custom fileds added by the plugin under the 
[ticket-custom] section.

The lines to remove should look something like this:
	completed = text
	completed.label = Date Completed
	completed.order = 9110
	storypoints = select
	storypoints.label = Storypoints
	storypoints.options = |0|0.5|1|2|3|5|8|13|21|34|55
	storypoints.order = 9100
	userstory = text
	userstory.label = User Story
	userstory.order = 9120

OTHER PLUGINS OF POSSIBLE INTEREST

CalendarPopUpPlugin (http://trac-hacks.org/wiki/CalendarPopUpPlugin)

	Provides a convienent javascript calendar widget that lets you select dates for fields in 
	trac.  This can be convienent for use in the completed date filed of trac tickets using
	the TracStoryPoint plugin.
	
	To configure this for use install it as usual and add the following lines to your sites
	trac.ini file:
	
	[calendarpopup]
	ids=field-completed=MM/dd/yyyy
	files=ticket.html

