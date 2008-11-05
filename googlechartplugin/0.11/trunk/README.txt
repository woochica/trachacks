===================
Google Chart Plugin
===================

This plugin provides a macro that uses the Google Chart API to graph the
result of any catalog query.

It uses the GChartWrapper library, which must be installed as a
dependency - see http://code.google.com/p/google-chartwrapper.

To use the plugin, use a macro like this in the wiki:

  [[GChart(query="SELECT id FROM ticket", type="line")]]

NOTE: This uses python dictionary syntax, so you need to quote strings,
but you can have commas wherever you want, and you can create lists and
tuples.

You can pass additional parameters as well. See the Google Chart Wrapper
and/or the Google Chart API (http://code.google.com/apis/chart/):

  [[GChart(type="bvs", chtt="My title" chco="4d89f9,c6d9fd", query="SELECT id, (time - 1225107400) FROM ticket")]]

If you'd like columns from the result set to be used as axis labels, or you
want to auto-scale the values (you either need to set a scale manually or
provide numbers in a range of 0..100 (i.e. a percentage) otherwise), then
describe your columns like so:

  [[GChart(type="bvs", colmns=[('x', 'labels'), ('y', 'scaled')], query="SELECT label, value FROM my_table")]]

If you give a list of columns, it must cover all the columns in the query.
The first argument is an axis for the column ('x', 'y', 't' or 'r' - each can
occur multiple times). The second argument is either 'labels', 'scaled' or
'percentage'.

If you want to specify a scale explicitly, you can do:

    columns=[('x', 'labels'), ('y', 'scaled', 0, 250)]

Installation
------------

Install GChartWrapper:

 $ easy_install --find-links http://code.google.com/p/google-chartwrapper GChartWrapper

and the install gchartplugin:

 $ python setup.py install

Then enable the plugin in trac.ini with::

 [components]
 gchartplugin.* = enabled
