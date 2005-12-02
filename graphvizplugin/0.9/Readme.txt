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

The different programs can be invoked using:

#!graphviz

#!graphviz.dot

#!graphviz.neato

#!graphviz.twopi

#!graphviz.circo

#!graphviz.fdp


Currently only PNG image files are supported and there is no way to
specify the default graph, node and edge attributes. Ideally, this
will be changed in a future release.


Installation via Source
=======================

todo


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

    dot_cmd - The command used to invoke graphviz's dot program.

    neato_cmd - The command used to invoke graphviz's neato program.

The cache_dir and prefix_url entries are related to each other. The
cache_dir entry points to a location on the file system and the
prefix_url points to the same location but from the trac server's
point of view. This allows the graphviz programs to generate the
images and the user's web browser to view them.

The cache_dir and tmp_dir directories must exist and the trac server
must have read and write access.


Configuration Example
+++++++++++++++++++++

Here is a sample graphviz section:

[graphviz]
cache_dir = /tmp/trac/htdocs/graphviz
prefix_url = http://localhost:8000/trac/chrome/site/graphviz
tmp_dir = /tmp/trac.graphviz
dot_cmd = dot
neato_cmd = neato
