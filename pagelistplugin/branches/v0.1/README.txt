Trac PageList Plugin
--------------------

Description
===========

The PageList plugin for Trac provides a wiki syntax extension to
create dynamic list of wiki names that match a specific string.

For example, 

    pagelist:HowTo

would list all the wiki pages that end with HowTo.


Installation via Source
=======================

The installation of the PageList plugin from source is done by
creating a Python egg distribution file and copying the .egg file to
the Trac plugins directory. Detailed information on Python eggs can be
found at: http://peak.telecommunity.com/DevCenter/PythonEggs. In
addition, the Easy Install package is required to create Python
eggs. See http://peak.telecommunity.com/DevCenter/EasyInstall for more
information on using and installing Easy Install.

Download the source code for the PageList plugin from
http://trac-hacks.swapoff.org/download/pagelistplugin.zip or checkout
the source from the trac hacks subversion repository at:
http://trac-hacks.swapoff.org/svn/pagelistplugin.

Change to the pagelistplugin/0.9 directory and run:

    python setup.py bdist_egg

This will generate a python egg in the dist directory. Copy the egg
file into the trac/plugins directory and follow the Configuration
steps outlined below.


Configuration
=============

Once installed, no special configuration is required.


Syntax
======

There are two forms available for using PageList. The first is as a
wiki syntax and the second is as request handler.

PageList Wiki Syntax
--------------------

The basic syntax is:

    pagelist:text

where the occurance of text within a wiki name is used as the
selection criteria.

There are two simple extensions to match a prefix or suffix:

    pagelist:prefix:text

would match all wiki names that start with text.

    pagelist:suffix:text

would match all wiki names that end with text.

The match is case sensitive.


PageList Request Handler
------------------------

The PageList plugin also implements a request handler called
pagelist. This can be used in a URL in the form of:

  http://host/pagelist/text

This would create a page that lists the wiki names that contain text.

There are two simple extensions to match a prefix or suffix:

  http://host/pagelist/prefix/text

would match all wiki names that start with text.

  http://host/pagelist/suffix/text

would match all wiki names that end with text.

As with the wiki syntax, matching is case sensitive.


Contributors
============

I'd like to extend my thanks to Alec Thomas for creating Trac Hacks
(http://trac-hacks.swapoff.org) and providing hosting for the PageList
plugin.


$Id: Readme.txt 533 2006-03-22 17:01:20Z pkropf $
