= Wiki Goodies for Trac =

== Description ==

This plugin extends the Trac Wiki in several ways:
 * Support for displaying smileys, as in 
   [http://moinmoin.wikiwikiweb.de/HelpOnSmileys MoinMoin]
 * Support for inserting HTML 4.0 entities
 * Support for replacing common text idioms by their corresponding symbols
   (e.g. arrows, fractions, etc.)


== Bugs/Feature Requests == 

Existing bugs and feature requests for WikiGoodiesPlugin are 
[report:9?COMPONENT=WikiGoodiesPlugin here].

If you have any issues, create a 
[http://trac-hacks.swapoff.org/newticket?component=WikiGoodiesPlugin&owner=cboos new ticket].

== Download ==

Download the zipped source from [download:wikigoodiesplugin here].

== Source ==

You can check out the source for WikiGoodiesPlugin from Subversion at http://trac-hacks.swapoff.org/svn/wikigoodiesplugin.

== Example ==

There are 3 new macros that can be used
to conveniently display all the newly introduced markup.

Simply copy&paste the following wiki snippet somewhere into your Wiki
(e.g. in WikiFormatting):
{{{
== Additional Goodies ==
=== Smileys ===
[[ShowSmileys(5)]]
=== Entities ===
[[ShowEntities(5)]]
=== Symbols ===
[[ShowSymbols(5)]]
}}}
''(the argument is the number of columns to be used in the displayed table)''


=== Known Issues ===

That plugin will only be compatible with Trac-0.9.3, 
which is not yet released...

But it also works for the trunk (!r2713 as of this writing).
However, in order to support the HTML 4.0 entities, this 
additional patch is required:
{{{
Index: trac/wiki/formatter.py
===================================================================
--- trac/wiki/formatter.py      (revision 2713)
+++ trac/wiki/formatter.py      (working copy)
@@ -144,7 +144,6 @@
     # between _pre_rules and _post_rules

     _pre_rules = [
-        r"(?P<htmlescape>[&<>])",
         # Font styles
         r"(?P<bolditalic>%s)" % BOLDITALIC_TOKEN,
         r"(?P<bold>%s)" % BOLD_TOKEN,
@@ -160,6 +159,7 @@
         r"(?P<htmlescapeentity>!?&#\d+;)"]

     _post_rules = [
+        r"(?P<htmlescape>[&<>])",
         # shref corresponds to short TracLinks, i.e. sns:stgt
         r"(?P<shref>!?((?P<sns>%s):(?P<stgt>%s|%s(?:%s*%s)?)))" \
         % (LINK_SCHEME, QUOTED_STRING,
}}}


=== See Also ===

The EmoticonsPlugin also provides support for smileys, and is 
a little bit more lightweight than this plugin.



== Author/Contributors ==

'''Author:''' [wiki:cboos] [[BR]]
'''Contributors:'''



