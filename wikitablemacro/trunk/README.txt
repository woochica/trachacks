=================
Wiki Table Plugin
=================

This plugin allows you to query the Trac database with a SQL query and
display the results as a table in a wiki page.

Usage::

    {{{
        #!SQLTable
            SELECT count(id) as 'Number of Tickets'
            FROM ticket
    }}}

This will create a table with one row and one column. You can obviously
create more complex queries as you wish.

Installation
------------

Install as normal, using easy_install or 'python setup.py install'. Then
add this to trac.ini::

    [components]
    wikitable.* = enabled