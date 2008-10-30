====================
SQL Constants Plugin
====================

Often, reports and other queries need to use constants. It is better to store
these in the database, rather than hard-coding them into multiple reports or
queries. This plugin provides an administration control panel where constants
can be maintained.

Before the plugin can be used, you must create a database table like this::

	CREATE TABLE `constants` (
	  `constant` varchar(255) NOT NULL,
	  `stringval` varchar(255) DEFAULT NULL,
	  `intval` int(11) DEFAULT NULL,
	  `floatval` float DEFAULT NULL,
	  PRIMARY KEY (`constant`)
	);

The web gui will always store a string value in stringval. If the entered
value can be converted to an integer and/or float, these will be stored as
well, otherwise they will be NULL.

To use a named constant in a report, either use a subquery or a join to look
up the column by name, and then reference stringval, intval or floatval as
appropriate.

Installation
------------

Install using 'setup.py install' or easy_install as normal, and then
enable in trac.ini with:

	[components]
	sqlconstants.* = enabled
	
If you want to use a different table name than 'constants', you can do::

	[sql-constants]
	table_name = some_name