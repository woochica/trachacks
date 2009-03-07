= LuntbuildTracIntegration =

A Trac plugin to show Luntbuild builds on the timeline page

== Building LuntbuildTracIntegration ==

{{{
$ cd /path/to/LuntbuildTracIntegration
$ python setup.py bdist_egg
$ cp dist/*.egg /path/to/projenv/plugins
}}}

for more info see http://trac.edgewall.org/wiki/TracDev/PluginDevelopment

== Luntbuild ==

This plugin has been tested against luntbuild 1.3.5 and 1.4.0, if the database 
schema changes in the future then this plugin may break.
                      
== Configuration ==

In order for this plugin to know where to look for your Luntbuild data we need to add 
some lines to your trac.ini file

{{{
[luntbuild]
db_host=localhost      # Mysql hostname where your luntbuild databas lives
db_name=luntbuild      # Mysql database name where the luntbuild schema is
db_user=luntbuild      # Mysql user used to connect
db_password=luntbuild  # Mysql user's password used to connect
base_url=/luntbuild    # URL used to link to Luntbuild can be relative or absolute
}}}

== Author ==

Written by David Roussel

