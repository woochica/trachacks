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

There are also several additional examples available in the examples
directory.  They can be loaded into a Trac installation by the
examples/load_examples.py program. Once loaded, navigate to the
wiki/GraphvizExamples page to access the examples.


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


Platform Specific Requirements
==============================

FreeBSD
+++++++

On FreeBSD systems, installing the x11-fonts/urwfonts package will
provide the fonts needed for graphviz to correctly generate images.


Optional requirements
=====================

To allow antialiasing of PNG images produced by graphviz, you need to
have rsvg, the librsvg rasterizer, installed on your system. It can be
downloaded from <http://librsvg.sourceforge.net/>. Note that rsvg is
not available for Windows.


Installation via Source
=======================

The installation of the graphviz plugin from source is done by
creating a Python egg distribution file and copying the .egg file to
the Trac plugins directory. Detailed information on Python eggs can be
found at: http://peak.telecommunity.com/DevCenter/PythonEggs. In
addition, the Easy Install package is required to create Python
eggs. See http://peak.telecommunity.com/DevCenter/EasyInstall for more
information on using and installing Easy Install.

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

    cache_dir       - The directory that will be used to cache the 
                      generated images.

    cmd_path        - Full path to the directory where the graphviz
                      programs are located. If not specified, the
                      default is /usr/bin on Linux, c:\Program
                      Files\ATT\Graphviz\bin on Windows and
                      /usr/local/bin on FreeBSD 6.

    out_format      - Graph output format. Valid formats are: png, jpg,
                      svg, svgz, gif. If not specified, the default is
                      png. This setting can be overrided on a per-graph
                      basis.

    processor       - Graphviz default processor. Valid processors
                      are: dot, neato, twopi, fdp, circo. If not
                      specified, the default is dot. This setting can
                      be overrided on a per-graph basis.

                      GraphvizMacro will verify that the default
                      processor is installed and will not work if it
                      is missing. All other processors are optional.
                      If any of the other processors are missing, a
                      warning message will be sent to the trac log and
                      GraphvizMacro will continue to work.

    png_antialias   - If this entry exists in the configuration file,
                      then PNG outputs will be antialiased.

    rsvg_path       - Full path to where the rsvg binary can be found.
                      The default is cmd_path + rsvg.

    default_*       - These settings define the default graph, node and
                      edge attributes. They must be written as :
                            default_TYPE_ATTRIBUTE = VALUE
                      where TYPE      is one of graph, node, edge
                            ATTRIBUTE is a valid graphviz attribute
                            VALUE     is the attribute value.
                        eg: default_edge_fontname = "Andale Mono"
                            default_graph_fontsize = 10

    cache_manager   - If this entry exists in the configuration file,
                      then the cache management logic will be invoked
                      and the cache_max_size, cache_min_size,
                      cache_max_count and cache_min_count must be
                      defined.

    cache_max_size  - The maximum size in bytes that the cache should
                      consume. This is the high watermark for disk space
                      used.

    cache_min_size  - When cleaning out the cache, remove files until
                      this size in bytes is used by the cache. This is
                      the low watermark for disk space used.

    cache_max_count - The maximum number of files that the cache should
                      contain. This is the high watermark for the
                      directory entry count.

The cache_dir directory must exist and the trac server must have read
and write access.

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
png_antialias = true
default_graph_fontname = "Andale Mono"
default_graph_fontsize = 10


Here is a sample graphviz section that activates the cache manager:

[graphviz]
cache_dir = /tmp/trac/htdocs/graphviz
png_antialias = true
default_graph_fontname = "Andale Mono"
default_graph_fontsize = 10
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


Here's the same example but for Windows systems:

[graphviz]
cache_dir = C:\projects\plugins\env\trac\htdocs\graphviz
cache_manager = yes
cache_max_size = 10000000
cache_min_size = 5000000
cache_max_count = 2000
cache_min_count = 1500

Notice that the png_antialias, rsvg_path, default_graph_fontname and
default_graph_fontsize are not defined. This is because rsvg is not
available on Windows and these options are not used.


Contributors
============

I'd like to extend my thanks to following people:

 * Kilian Cavalotti for

   * the code to allow the output format to be specified system wide and 
     per diagram.

   * work on the code to expand Trac wiki links within Graphviz
     diagrams.

 * Alec Thomas for creating Trac Hacks (http://trac-hacks.swapoff.org)
   and providing hosting for the Graphviz module.

 * Emmanuel Blot for the swift kick in the butt to get the 0.9 - 0.10
   releated bug fixes resolved ;-)


$Id$
