= iCalExporterPlugin = 

== Description ==

'''read trac feeds in your calendar'''

For out of the box trac, only the [http://trac.edgewall.org/roadmap roadmap module] has an [http://trac.edgewall.org/roadmap?format=ics iCal feed].  the IcalExporterPlugin exposes an [http://ietf.org/rfc/rfc2445.txt iCal format] in the ''"Download in other formats"'' section.  The calendar is created by parsing the RSS feed for the page and transforming it to iCal format.  The calendar can then be read by (e.g.) [http://google.com/calendar google calendar] by using the [http://google.com/support/calendar/bin/answer.py?hl=en&answer=37100 "Add by URL"] feature.  

== Installation == 

The homepage for this plugin is at
http://trac-hacks.org/wiki/IcalExporterPlugin with links to the
subversion repository and zipped eggs.  The plugin is installed in the
standard way.  For more information, see http://trac.edgewall.org/wiki/TracPlugins

== How it Works ==

The IcalExporterPlugin examines if a page has an RSS feed.  If it does, it adds a iCalendar download option as well.  The brunt of the work is done by [/svn/icalexporterplugin/0.11/icalexporter/ical.py ical.py], which writes the iCalendar format (most of the hard work was stolen from [http://trac.edgewall.org/browser/trunk/trac/ticket/roadmap.py the roadmap module]).  [/svn/icalexporterplugin/0.11/icalexporter/ical.py ical.py] is independent of trac and should probably be moved upstream of the plugin or of trac entirely.
