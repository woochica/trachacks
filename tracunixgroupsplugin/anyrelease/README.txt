= TracHtgroups =

A permission group provider for Trac. It is using Unix group 
membership 

== Installation ==
 1. Run: python setup.py bdist_egg
 2. If necessary create a folder called "plugins" in your Trac environment.
 3. Copy the .egg file from the dist folder created by step 1 into the
    "plugins" directory of your Trac environment.

== Configuration ==
None

All unix groups will be translated to trac grops by prefixing with '@'. E.g. Unix group 'developers' could be refered inside trac as '@developers'

== Thanks ==

Based on http://trac-hacks.org/wiki/HtgroupsPlugin

