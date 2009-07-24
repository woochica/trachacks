= icalviewplugin = 

== Description ==

'''export ticket queries as icalendar'''

Provide iCalendar feeds for ticket queries like [http://trac.edgewall.org/roadmap roadmap module]. It use 2 custom fields for event date and duration (in days).

GPL

== Installation == 

The homepage for this plugin is at
http://trac-hacks.org/wiki/IcalExporterPlugin with links to the
subversion repository and zipped eggs.  The plugin is installed in the
standard way.  For more information, see http://trac.edgewall.org/wiki/TracPlugins

== How it Works ==

The iCanViewPlugin use the Query syntax to provide an iCalendar view for ticket queries. It needs two custom field for etting event date (date_start) and event duration in days (duration). It provide a link in ticket's queries footer and an /ical?.. urls (usefull for specific apache authentication config).

