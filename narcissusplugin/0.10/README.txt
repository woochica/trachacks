 Trac Narcissus Plugin
---------------------

Description
===========

Narcissus is a plugin for Trac that provides an interactive visualisation
for mirroring the activities of small groups over a period of months.
The activities are measured differently for each resource. Contributions to 
the wiki and Subversion repository are measured according to the number of 
added lines. Tickets are scored according to the type of activity, such as 
creating, accepting, and resolving tickets, as well as adding comments at 
different stages of the task.

Users have the ability to control the value placed in each activity. The
underlying measures of the visualisations are very simple; it is important 
that this is clear to the users. 


Requirements
============

The narcissus plugin requires the Python Imaging Library (PIL) to
produce PNG images, and must be installed on your system. It can 
be downloaded from http://www.pythonware.com/products/pil.


Optional requirements
=====================

Any TrueType font may be used for the narcissus visualisations. Microsoft's
TrueType core fonts can be downloaded from http://corefonts.sourceforge.net/
for Linux and from http://web.nickshanks.com/typography/corefonts for Mac
or Windows systems.


Installation via Source
=======================

The installation of the narcissus plugin from source is done by
creating a Python egg distribution file and copying the .egg file to
the Trac plugins directory. Detailed information on Python eggs can be
found at http://peak.telecommunity.com/DevCenter/PythonEggs. In
addition, the Easy Install package is required to create Python
eggs. See http://peak.telecommunity.com/DevCenter/EasyInstall for more
information on using and installing Easy Install.

Checkout the source code for the narcissus plugin from:
http://praxis.it.usyd.edu.au/svn/kim/hons/Project/narcissus-plugin

Change to the narcissusplugin/0.10 directory and run:

python setup.py bdist_egg

This will generate a python egg in the dist directory. Copy the egg
file into the trac/plugins directory and follow the Configuration
steps outlined below.

We are currently looking at adding the narcissus plugin to the
swapoff repository hosted by http://trac-hacks.org/ in the future,
as the plugin matures.

Configuration
=============

Once the narcissus plugin has been installed either via source or via a
python egg, some configuration is needed before it can be used.

A new section called narcissus should be added to the conf/trac.ini
file with these fields:

cache_dir - The directory that will be used to cache the 
			generated images.

cache_manager - If this entry exists in the configuration file,
			then the cache management logic will be invoked
			and the cache_max_size, cache_min_size,
			cache_max_count and cache_min_count must be
			defined.

cache_max_size - The maximum size in bytes that the cache should
			consume. This is the high watermark for disk space
			used.

cache_min_size - When cleaning out the cache, remove files until
			this size in bytes is used by the cache. This is
			the low watermark for disk space used.

cache_max_count - The maximum number of files that the cache should
			contain. This is the high watermark for the directory
			entry count.

ttf_path - The path (including directory and filename) of the
			TrueType font to be used for visualisation. Optional.

The cache_dir directory must exist and the Trac server must have read
and write access.

The cache manager is an attempt at keeping the cache directory under
control. This is experimental code that may cause more problems than
it fixes. The cache manager will be invoked only if a new Narcissus
image is to be produced. If the image can be loaded from the cache,
then the cache manager shouldn't need to run. This should minimize the
I/O performance impact on the trac server. When the cache manager
determines that it should clean up the cache, it will delete files
based on the file access time. The files that were least accessed will
be deleted first.

Note: it is also recommended that the restrict_owner field under the 
ticket section of the configuration file should be set to true, in 
order to get the most out of the ticket view of the visualisation:

[ticket]
restrict_owner = true


Configuration Example
+++++++++++++++++++++

Here is a sample narcissus section:

[narcissus]
cache_dir = /tmp/trac/htdocs/narcissus
cache_manager = yes
cache_max_size = 10000000
cache_min_size = 5000000
cache_max_count = 2000
cache_min_count = 1500
ttf_path = /usr/share/fonts/truetype/msttcorefonts/arial.ttf

Note: /tmp may be cleaned after reboot depending on your platform and 
system preferences, which implies that the cache directory would need 
to be recreated after a reboot if it has been set to the above example.

The cache manager is turned on since there is an entry in the narcissus
section called cache_manager. The value doesn't matter. To turn off
the cache manager, simply comment out the cache_manager entry.

When the size of all the files in the cache directory exceeds
10,000,000 bytes or the number of files in the cache directory exceeds
2,000, then files are deleted until the size is less than 5,000,000
bytes and the number of files is less than 1,500.

Here's the same example but for Windows systems:

[narcissus]
cache_dir = C:\projects\plugins\env\trac\htdocs\narcissus
cache_manager = yes
cache_max_size = 10000000
cache_min_size = 5000000
cache_max_count = 2000
cache_min_count = 1500
ttf_path = C:\windows\fonts\arial.ttf


Contributors
============

Some of the source code in the narcissus plugin was adapted from:

 * Trac/Timeline.py, Copyright (c) Edgewall Software
 * The graphviz plugin, Copyright (c) Peter Kropf
 * The peerreview plugin, Copyright (C) Team5
 
Many thanks to Trent Apted for random smatterings of help and advice.