Trac Graphviz Wiki Processor
----------------------------

Description
===========

The graphviz wiki processor is a plugin for Trac that allows the the
dynamic generation of diagrams by the various graphviz programs. The
text of a wiki page can contain the source text for graphviz and the
web browser will show the resulting image.


Simple Example
++++++++++++++

A simple example would be:

{{{
#!graphviz
digraph G {Hello->World->Graphviz->Rules}
}}}


Usage Details
+++++++++++++

The graphviz wiki processor supports all 5 graphviz drawing programs:
dot, neato, twopi, circo and fdp. By default, the dot program is used
to generate the images.

The different programs can be invoked using one of these:

#!graphviz
#!graphviz.dot
#!graphviz.neato
#!graphviz.twopi
#!graphviz.circo
#!graphviz.fdp


The supported image formats are: png (default), gif, jpg, svg and svgz.
The format can be specified using a "/format" modifier, in the hashbang,
as shown below:

#!graphviz/svg
#!graphviz.dot/png
#!graphviz.circo/gif


Currently there is no way to specify the default graph, node and 
edge attributes. Ideally, this will be changed in a future release.


Installation via Source
=======================

Download the source code for the graphviz plugin from
http://trac-hacks.swapoff.org/download/graphvizplugin.zip or checkout
the source from the trac hacks subversion repository at:
http://trac-hacks.swapoff.org/svn/graphvizplugin.

Change to the graphvizplugin/0.9 directory and run:

    python setup.py bdist_egg

This will generate a python egg in the dist directory. Copy the egg
file into the trac/plugins directory and follow the Configuration
steps outlined below.


Installation via Egg
====================

todo


Configuration
=============

Once the graphviz plugin has been installed either via source or via a
python egg, some configuration is needed before it can be used.

A new section called graphviz should be added to the conf/trac.ini
file with these fields:

    cache_dir - The directory that will be used to cache the generated
                images.

    prefix_url - The url to be used to find the cached images. This
                 must point to the trac server's view of the cache_dir
                 location.

    tmp_dir - A temporary directory used in the processing of the
              graphviz documents.

    cmd_path - Full path to the directory where the graphviz programs
               are located.

    out_format - Graph output format. Valid formats are : png, jpg, svg, 
                 svgz, gif. If not specified, the default is png.

    cache_manager - If this entry exists in the configuration file,
                    then the cache management logic will be invoked
                    and the cache_max_size, cache_min_size,
                    cache_max_count and cache_min_count must be
                    defined.

    cache_max_size - The maximum size in bytes that the cache should
                     consume. This is the high watermark for disk
                     space used.

    cache_min_size - When cleaning out the cache, remove files until
                     this size in bytes is used by the cache. This is
                     the low watermark for disk space used.

    cache_max_count - The maximum number of files that the cache
                      should contain. This is the high watermark for
                      the directory entry count.

    cache_min_count - When cleaning out the cache, remove files until
                      this number of files remain in the cache. This
                      is the low watermark for the directory entry
                      count.

The cache_dir and prefix_url entries are related to each other. The
cache_dir entry points to a location on the file system and the
prefix_url points to the same location but from the trac server's
point of view. This allows the graphviz programs to generate the
images and the user's web browser to view them.

The cache_dir and tmp_dir directories must exist and the trac server
must have read and write access.

The cache manager is an attempt at keeping the cache directory under
control. This is experimental code that may cause more problems than
it fixes. The cache manager will be invoked only if a new graphviz
image is to be produced. If the image can be loaded from the cache,
then the cache manager shouldn't need to run. This should minimize the
I/O performance impact on the trac server. When the cache manager
determines that it should clean up the cache, it will delete files
based on the file access time. The files that were least accessed will
be deleted first.


Configuration Example
+++++++++++++++++++++

Here is a sample graphviz section:

[graphviz]
cache_dir = /tmp/trac/htdocs/graphviz
prefix_url = http://localhost:8000/trac/chrome/site/graphviz
tmp_dir = /tmp/trac.graphviz
cmd_path = /usr/bin
out_format = png


Here is a sample graphviz section that activates the cache manager:

[graphviz]
cache_dir = /tmp/trac/htdocs/graphviz
prefix_url = http://localhost:8000/trac/chrome/site/graphviz
tmp_dir = /tmp/trac.graphviz
cmd_path = /usr/bin
out_format = png
cache_manager = yes
cache_max_size = 10000000
cache_min_size = 5000000
cache_max_count = 2000
cache_min_count = 1500

The cache manager is turned on since there is an entry in the graphviz
section called cache_manager. The value doesn't matter. To turn off
the cache manager, simply comment out the cache_manager entry.

When the size of all the files in the cache directory exceeds
10,000,000 bytes or the number of files in the cache directory exceeds
2,000, then files are deleted until the size is less than 5,000,000
bytes and the number of files is less than 1,500.


Contributors
============

I'd like to extend my thanks to following people:

    - Kilian Cavalotti for the code to allow the output format to be
      specified system wide and per diagram.

    - Alec Thomas for creating Trac Hacks
      (http://trac-hacks.swapoff.org) and providing hosting for the
      Graphviz module.


$Id$
