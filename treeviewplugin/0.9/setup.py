from setuptools import find_packages, setup

from setuptools import setup

PACKAGE = 'TreeView'
VERSION = '0.3'

setup(
  name          = PACKAGE,
  version       = VERSION,
  author        = 'Simon Drabble',
  author_email  = 'tracplugins@thebigmachine.org',
  license       = 'GPL',
  keywords      = 'trac plugin wiki tree view',
  description   = 'Display a hierarchical tree of information',
  long_description = """

  == Summary ==

  This plugin provides the ability to display a neat rendering of any
  hierarchical data structure such as a set of files within a file system,
  hosts on a network, or similar.

  == Syntax ==


  The plugin adds the following syntactic elements to the wiki processor:

  +-
  --

  +- is the token to begin a new tree or continue one in progress.

  Add entries with

  +-*name

  * is some separator character (e.g. / for directories, . for parts of
  a domain name, or any other character except for whitespace)
  name is some unique identifier within the current tree, possibly containing
  further separators and names (nodes).

  A tree's entries are ended with --. If -- is seen but the processor is not in
  'capture tree nodes' mode, -- will be rendered as-is.


  == Features ==

   * Attempts will be made by the plugin to disambiguate nodes following
     deterministic rules, so only the information necessary to uniquely identify
     a parent node need be provided when adding further nodes.

   * Nodes may be designated as 'terminal' or 'container'. Container nodes
     obviously contain further nodes, but otherwise-terminal nodes may be
     marked as containers for display purposes.

   * When a tree is displayed in a wiki page, entire sub-trees may be
     collapsed/ expanded as desired. The whole tree is considered a subtree,
     so the collapse/ expand rule applies just as well to it as to any other.
     (requires javascript)

   * Intermediate nodes are created on demand. There is no need to separately
     specify each and every child node in a long branch.

   * Comments may be added to terminal nodes (or empty container nodes).


  == Examples ==

  See the README file accompanying this distribution for examples.

  == Known Bugs ==

   * The use of &nbsp;s to render nicely lined-up HTML is kinda ugly.
     I'd like to replace it with CSS, but tests show that the CSS variant
     (a naive implementation, to be sure) results in larger HTML size
     than the &nbsp variant.

  == TODO ==

   * Config-file options for syntactic elements (+, >, V etc)

  == Limitations ==

   * Whitespace cannot be used as a node delimiter.
   * Duplicate children of a parent node are not supported.
   * Cyclical hierarchies are not supported.

  """,
  platform      = 'Any',
  packages      = ['treeview'],
  entry_points  = { 'trac.plugins': '%s = treeview' % PACKAGE },
)
