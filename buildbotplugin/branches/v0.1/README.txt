Trac Buildbot Plugin
--------------------

Description
===========

The buildbot plugin for Trac provides access to the state of a
buildbot master and slaves.


Installation via Source
=======================

The installation of the buildbot plugin from source is done by
creating a Python egg distribution file and copying the .egg file to
the Trac plugins directory. Detailed information on Python eggs can be
found at: http://peak.telecommunity.com/DevCenter/PythonEggs. In
addition, the Easy Install package is required to create Python
eggs. See http://peak.telecommunity.com/DevCenter/EasyInstall for more
information on using and installing Easy Install.

Download the source code for the buildbot plugin from
http://trac-hacks.swapoff.org/download/buildbotplugin.zip or checkout
the source from the trac hacks subversion repository at:
http://trac-hacks.swapoff.org/svn/buildbotplugin.

Change to the buildbotplugin/0.9 directory and run:

    python setup.py bdist_egg

This will generate a python egg in the dist directory. Copy the egg
file into the trac/plugins directory and follow the Configuration
steps outlined below.


Configuration
=============

TODO


Contributors
============

I'd like to extend my thanks to following people:

 * Alec Thomas for creating Trac Hacks (http://trac-hacks.swapoff.org)
   and providing hosting for the Buildbot plugin.


$Id: Readme.txt 533 2006-03-22 17:01:20Z pkropf $
