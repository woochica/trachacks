Trac MetaPost Wiki Processor
----------------------------

Description
===========

The metapost wiki processor is a plugin for Trac that allows the the
dynamic generation of MetaPost diagrams. The
text of a wiki page can contain the source text for graphviz and the
web browser will show the resulting image.


Simple Example
++++++++++++++

A simple example would be::

  #!metapost
  input metauml;
  beginfig(1);

  Begin.b;
  State.On("On")();
  State.Off("Off")();
  End.e;

  leftToRight(20)(b, On, Off, e);

  drawObjects(b, On, Off, e);

  clink(transition)(b, On);
  clink(transition)(On, Off);
  clink(transition)(Off, e);

  endfig;
  end


There are also several additional examples available in the examples
directory.  They can be loaded into a Trac installation by the
examples/load_examples.py program. Once loaded, navigate to the
wiki/MetapostExamples page to access the examples.


Usage Details
+++++++++++++

The metapost wiki processor supports 4 output image types: png (default),
gif, jpg (and jpeg) and svg.
The format can be specified using a "/format" modifier, in the hashbang,
as shown below::

 #!metapost/svg
 #!metapost/png
 #!metapost/gif
 
 
Platform Requirements
==============================

Following commands should be available for execution:
mpost,
mptopdf,
pdftoppm,
pdf2svg


Installation via Source
=======================

The installation of the metapost plugin from source is done by
creating a Python egg distribution file and copying the .egg file to
the Trac plugins directory. Detailed information on Python eggs can be
found at: http://peak.telecommunity.com/DevCenter/PythonEggs. In
addition, the Easy Install package is required to create Python
eggs. See http://peak.telecommunity.com/DevCenter/EasyInstall for more
information on using and installing Easy Install.

Download the source code for the metapost plugin from
http://trac-hacks.swapoff.org/download/metapostplugin.zip or checkout
the source from the trac hacks subversion repository at:
http://trac-hacks.swapoff.org/svn/metapostplugin.

Change to the metapostplugin/0.11 directory and run::

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
python egg, some changes to the conf/trac.ini file must be done before it can 
be used.

As for any plugin, if you did a global installation (as opposed to simply 
dropping the .egg in the plugins folder of your Trac environment), 
you first need to enable it::

   [components]
   metapost.* = enabled

A new section called ``[graphviz]`` should be added to the trac.ini
file with these fields::

    cache_dir       - The directory that will be used to cache the 
                      generated images. That directory must exist,
                      unless you keep the default 'gvcache' value,
                      in which case the plugin is allowed to create
                      the folder inside the Trac environment.

    out_format      - Graph output format. Valid formats are: png, jpg,
                      svg, svgz, gif. If not specified, the default is
                      png. This setting can be overrided on a per-graph
                      basis.

    default_*       - These settings define the default graph, node and
                      edge attributes. They must be written as:
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

Here is a sample graphviz section::

 [metapost]
 cache_dir = /tmp/trac/htdocs/graphviz


Here is a sample graphviz section that activates the cache manager::

 [metapost]
 cache_dir = /tmp/trac/htdocs/graphviz
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



$Id$
