= TracHtgroups =

A permission group provider for Trac.  It reads groups from a group file
used with Apache in it's AuthGroupFile/AuthDigestGroupFile directive.

== Installation ==
 1. Run: python setup.py bdist_egg
 2. If necessary create a folder called "plugins" in your Trac environment.
 3. Copy the .egg file from the dist folder created by step 1 into the
    "plugins" directory of your Trac environment.

== Configuration ==
Add one of the following sections to trac.ini to use a group file with or
without the enhanced AccountManager plugin.

== With AccountManager ===
{{{
[account-manager]
password_format = htpasswd
password_file = /path/to/trac.htpasswd
group_file = /path/to/trac.groups
}}}

=== Without AccountManager ===
{{{
[htgroups]
group_file = /path/to/trac.groups
}}