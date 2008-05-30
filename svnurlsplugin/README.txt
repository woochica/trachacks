SVN URLs
========

The SVNURLsPlugin provides links to the url of repository files as viewable
at /browser, /log, and /changeset in trac.  This enables easy reference to the
actual svn entities for svn operations To make this work, you will
have to add a section in the trac.ini for your project.  

[svnurls]
svn_base_url = https://your.repository/location

Optionally, you may also add an entry to this section controlling what text
is displayed:

link_text = [svn]

The above is the default.

Where This Lives
----------------

SVN URLs lives at 

https://svn.openplans.org/svn/TracPlugins/svnurls/

