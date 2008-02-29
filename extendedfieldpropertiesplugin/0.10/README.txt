= TracExtendedFieldProperties =
    
A Trac plugin that provides more configuration options for ticket fields, both stock and custom fields, like labeling and hiding/skipping.

== Supported Trac versions ==

It has only being tested with 0.10.

== Installation ==

 1. Run: python setup.py bdist_egg
 2. If necessary create a folder called "plugins" in your Trac environment.
 3. Copy the .egg file from the dist folder created by step 1 into the "plugins"
    directory of your Trac environment.

== Configuration ==

Use label and skip options for fields in both {{{ticket}}} and {{{ticket-custom}}}
sections as explained in TracTicketsCustomFields.

