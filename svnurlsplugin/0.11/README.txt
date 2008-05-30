SVN URLs
========

= show SVN URL links in /browser, /log, and /changelog =

== Description ==

The SvnUrlsPlugin provides links to the url of repository files as
viewable
at /browser, /log, and /changelog in trac.  This enables easy
reference to the
actual svn entities for svn operations To make this work, you will
have to add a section in the trac.ini for your project.

{{{
[svn]
repository_url = https://your.repository/location
}}}

Optionally, you may also add an entry to this section controlling what
text
is displayed:

{{{
[svnurls]
link_text = [svn]
}}}

The above is the default.

== Bugs/Feature Requests == 

Existing bugs and feature requests for SvnUrlsPlugin are
[query:status!=closed&component=SvnUrlsPlugin&order=priority here].

If you have any issues, create a 
[/newticket?component=SvnUrlsPlugin&owner=k0s new ticket].

== Download and Source ==

Download the [download:svnurlsplugin zipped source], check out
[/svn/svnurlsplugin using Subversion], or [source:svnurlsplugin browse
the source] with Trac.

== Example ==

See http://trac.openplans.org/openplans/browser . The {{{[svn]}}}
links in the image below point to the http svn location of the
relevant resources:

[[Image(svnurls.png)]]

== How SVN URLs Works ==

svnurls filters the outgoing stream using ITemplateStreamFilter.  This
requires the latest version of genshi.  Running {{{python setup.py
[develop|install]}}} should pull down the correct version 
