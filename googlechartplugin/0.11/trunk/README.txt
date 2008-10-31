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

If you'd like columns from the result set to be used as axis labels (bar,
line and scatter charts), you can specify the index (starting at 0) of the
column, e.g.::

  [[GChart(type="bvs", query="SELECT label, value FROM my_table", xlabels=0)]]

The possible axes are xlabels, ylabels, tlabels (top) and rlabels (right).

When constructing a query, it should return columns of numbers - other data
will be ignored. By default, each column is treated as a chart data set, using
text encoding. Multiple columns will result in multiple data sets.

If instead you want each row to be a data set, where each column provides one
data value, pass `tuples=True` as an argument.

Installation
------------

Install GChartWrapper:

 $ easy_install --find-links http://code.google.com/p/google-chartwrapper GChartWrapper

and the install gchartplugin:

 $ python setup.py install

Then enable the plugin in trac.ini with::

 [components]
 gchartplugin.* = enabled
