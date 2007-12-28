============
TracPerforce - A Perforce version control plugin for Trac.
============

Features:

 * Browse a Perforce directory hierarchy
 * Display source file contents
 * Display file and directory diffs
 * Specify revisions using change numbers, labels and dates
 * Browse revision logs for a file or directory
 * Repository checkins show up in the timeline
 * Changesets are cached in Trac's database
 * Changeset wiki links are marked up correctly
 * Scales to large Perforce repositories
 * Supports multi-threaded ModPython installations
 * Supports Unicode-enabled Perforce servers

Requirements:

 * Python 2.4 or later
   http://www.python.org/

 * Trac 0.11
   http://trac.edgewall.org/

 * setuptools 0.6c1 or later
   http://peak.telecommunity.com/DevCenter/EasyInstall

 * PyProtocols 0.9.3 or later
   http://peak.telecommunity.com/PyProtocols.html

 * PyPerforce 0.4 or later
   http://pyperforce.sourceforge.net/

Installation:

 * Download and install requirements.

 * Build the .egg file.

   Run:
   $ python setup.py bdist_egg

 * Install the .egg file
   
   For per-environment installation, copy the .egg file into the /plugins
   subdirectory of your Trac environment.

   For a global installation run 'python setup.py install'.

 * Configure your trac.ini file:

   Add these lines to the respective sections:

   [trac]
   repository_type = perforce
   repository_dir = /

   [perforce]
   port = perforce:1666
   user = p4trac
   password = secret
   unicode = 0  # or 1

 * Restart the Trac web server

   Note: Loading a page that uses the plugin for the first time can take
   a long time while the plugin populates the initial changeset cache,
   depending on the size of the Perforce repository.

   Alternatively you could run the following command to force an offline
   sync of the repository:
   $ trac-admin /path/to/trac/env resync

Future work:

 * Replication of Trac tickets to Perforce jobs

 * Per-user authentication and authorisation

 * Support for ticket based authentication and automated login

 * Fix 'created_rev' to report the revision of last 'edit',
   skipping 'copy' or 'move' revisions.

 * Add a 'fixes' property to changesets that lists tickets/jobs fixed
   by that change.

 * Add an 'integrations' property to changesets/files that lists integrated
   revisions merged in that revision.

 * Auto-detection of unicode Perforce servers

Credits:

 Written by Lewis Baker <lewisbaker@users.sourceforge.net>
 and by Thomas Tressieres <thomas.tressieres@free.fr>

 Thanks to these people for their input into this version and earlier versions
 of the Perforce plugin.

  * David Pearce
  * Jason Parks
  * Christian Boos
  * kenjin@clazzsoft.com
  * kristjan@ccpgames.com
