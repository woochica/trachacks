= Wiki Goodies for Trac =

== Description ==

This plugin extends the Trac Wiki in several ways:
 * Support for displaying smileys, as in 
   [http://moinmoin.wikiwikiweb.de/HelpOnSmileys MoinMoin],
   with a few exceptions (no flags, "priority" smileys are renamed {p1}
   instead of {1} in order to be compatible with report: shorthand links)
 * HTML 4.0 entities (named entities and numerical entities)
 * Automatic replacement of common text idioms by their corresponding symbols
   (e.g. arrows, fractions, etc.)
 * Simplified markup for single words: `*this* /is/ _important_`
   becomes '''this''' ''is'' __important__ [[comment(replace by *this* /is/ _important_)]]
 * Replace <name@domain> with "mailto:" links (obfuscated if needed)
 * Replace \\... UNC paths with "file:///" links 

Each feature can be disabled individually if needed.

In particular, turning off the UNC paths transformation might be seen as a
[http://kb.mozillazine.org/Links_to_local_pages_don%27t_work security measure].
Here, the "file:" links are user-oriented and can't be embedded in a <img>
or Javascript code, I don't really see what could be the risk, so I think 
it's OK to enable this feature.
Firefox users can use the [http://locallink.mozdev.org/ LocalLink] plugin
([https://addons.mozilla.org/en-US/firefox/addon/281 install]). 
Of course, if someone can demonstrate that this feature presents
a security risk, I'll disable it by default in future releases.


== Bugs/Feature Requests == 

Existing bugs and feature requests for WikiGoodiesPlugin are 
[report:9?COMPONENT=WikiGoodiesPlugin here].

Short list of known defects:
[[TicketQuery(status!=closed&component=WikiGoodiesPlugin&type=defect)]]

If you have any new issue of feature request, create a 
[http://trac-hacks.org/newticket?component=WikiGoodiesPlugin&owner=cboos new ticket].

== Download ==

Download the zipped source:
|| ''Trac Version'' || ''Zip'' ||
|| 0.9.3 and above, 0.10 || [download:wikigoodiesplugin/0.9]  ||
||          0.11         || [download:wikigoodiesplugin/0.11] ||

== Source ==

You can check out the source for WikiGoodiesPlugin from Subversion at http://trac-hacks.org/svn/wikigoodiesplugin.

== Example ==

There are 3 new macros that can be used
to conveniently display all the newly introduced markup.

Simply copy&paste the following wiki snippet somewhere into your Wiki
(e.g. in WikiFormatting):
{{{
=== Additional Goodies ===
==== Smileys ====
[[ShowSmileys(5)]]
==== Entities ====
[[ShowEntities(4)]]
==== Symbols ====
[[ShowSymbols(5)]]

}}}
''(the argument is the number of columns to be used in the displayed table)''

For the entities, only the named ones are shown.
For help on using the numerical entities, see for example those
[http://home.tiscali.nl/t876506/entitiesTips.html tips].

=== Known Issues ===


=== See Also ===

The EmoticonsPlugin also provides support for smileys, and is 
a little bit more lightweight than this plugin.



== Author/Contributors ==

'''Author:''' [wiki:cboos] [[BR]]
'''Contributors:'''



