= GeoTicket =

''add geolocations to Trac tickets''

== Requirements ==

 * [http://www.geopy.org/ geopy] for geolocation and reverse
   geolocation. This is pegged to a branch for
   [http://code.google.com/p/geopy/wiki/ReverseGeocoding reverse geolocation]
 * [http://postgis.refractions.net/ PostGIS] for geospatial queries


== Install ==

See [http://trac-hacks.org/svn/geoticketplugin/0.11/INSTALL]


== Components ==

 * [#GeoTicket GeoTicket] ''(`ticket.py`)''
 * [#GeoMailToTicket GeoMailToTicket] ''(`mail.py`)''
 * [#GeospatialQuery GeospatialQuery] ''(`query.py`)'' : requires PostGIS
 * [#GeoRegions GeoRegions] ''(`regions.py`)''
 * [#GeoNotifications GeoNotifications] ''(`web_ui.py`)''
 * [#IssueMap IssueMap] ''(`web_ui.py`)''
 * [#MapDashboard MapDashboard] ''(`web_ui.py`)''

=== !GeoTicket ===

=== !GeoMailToTicket ===

=== !GeospatialQuery ===

You will be able to query on radius from a geolocatable location.

If the [#GeoRegions GeoRegions] component is enabled and you have
succesfully uploaded [http://en.wikipedia.org/wiki/Shapefile shapefiles], 
you will be able to query based on regions.

=== !GeoRegions ===

=== !GeoNotifications ===

=== !IssueMap ===

=== !MapDashboard ===
