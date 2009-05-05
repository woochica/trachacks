= TracSysgroups =

A permission system-group provider for Trac.  It asks linux / unix system
to which groups a validated user belongs. If one of this groups matches
a permission group name created with "trac-admin permission add" command,
these permissions are enabled for logged-on user.

== Installation ==
 1. Run: python setup.py bdist_egg
 2. If necessary create a folder called "plugins" in your Trac environment.
 3. Copy the .egg file from the dist folder created by step 1 into the
    "plugins" directory of your Trac environment.

== Configuration ==
no configuration has to be done.
