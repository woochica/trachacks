= Wiki Extras for Trac =
[[PageOutline(2-5,Contents,pullout)]]


== Description ==

 '''''This plugin is made for the upcoming Trac 0.13, and will be updated along
 with changes to Trac 0.13dev! ''' [[BR]]
 (This plugin could work with Trac 0.12, but the visual impression may not be 
 as intended.) ''

The [http://trac-hacks.org/wiki/WikiExtrasPlugin WikiExtrasPlugin] extends the
Trac Wiki in several ways:

 * Layout information on wiki pages using boxes. Four wiki processors are
   defined for creating boxes:
   * `box` -- The core box processor.
   * `rbox` -- Display a right aligned box to show side notes and warnings etc.
     This will probably be the most used box.
   * `newsbox` -- Display news in a right aligned box. ''(This box corresponds
     to the well-known
     [http://trac-hacks.org/wiki/NewsFlashMacro NewsFlashMacro])''
   * `imagebox` -- Display a single image with caption in a centered box.
 * Decorate wiki pages with a huge set of modern icons via wiki markup
   `(|name|)`, or the equivalent `Icon` macro, and as smileys (smiley
   characters are configurable).
 * Decorate wiki text with the `Color` macro.
 * Automatic highlighting of attentional phrases like `FIXME` and `TODO`
   (configurable).
 * HTML 4.0 entities (named entities and numerical entities). ''(Same as in
   [http://trac-hacks.org/wiki/WikiGoodiesPlugin WikiGoodiesPlugin])''
 * Automatic replacement of common text idioms by their corresponding symbols
   (e.g. arrows, fractions, etc.) ''(Same as in
   [http://trac-hacks.org/wiki/WikiGoodiesPlugin WikiGoodiesPlugin], but
   configurable.)''

Each feature can be disabled individually if needed.


== Icon Library License Terms ==

The icon library contained in this plugin is composed of the
[http://p.yusukekamiyamane.com Fugue icon library] with additional icons, and
can be used for any commercial or personal projects, but you may not lease,
license or sublicense the icons. The icon library is provided for convenience,
though download and installation time is taking a hit since it contains more
than 3.000 unique icons in two flavors; shadowed and shadowless (yielding a
grand total of almost 7.000 icon files).

The [http://p.yusukekamiyamane.com Fugue icon library] is released under
[http://creativecommons.org/licenses/by/3.0/ Creative Commons Attribution 3.0 license].
[[BR]]
Some icons are Copyright (C) [http://p.yusukekamiyamane.com/ Yusuke Kamiyamane].
All rights reserved.

Additional icons are released under same
[http://trac.edgewall.org/licence.html license terms] as Trac.
[[BR]]
Some icons are Copyright (C) [http://www.edgewall.org Edgewall Software].
All rights reserved.


== See Also ==

[http://trac-hacks.org/wiki/ColorMacro ColorMacro],
[http://trac-hacks.org/wiki/EmoticonsPlugin EmoticonsPlugin],
[http://trac-hacks.org/wiki/NewsFlashMacro NewsFlashMacro],
[http://trac-hacks.org/wiki/TracFigureMacro TracFigureMacro] and
[http://trac-hacks.org/wiki/WikiGoodiesPlugin WikiGoodiesPlugin].


== Bugs / Feature Requests ==

Existing bugs and feature requests for
[http://trac-hacks.org/wiki/WikiExtrasPlugin WikiExtrasPlugin] are
[http://trac-hacks.org/report/9?COMPONENT=WikiExtrasPlugin here].

If you have any issues, create a 
[http://trac-hacks.org/newticket?component=WikiExtrasPlugin&owner=mrelbe new ticket].


== Download ==

Download the zipped source from
[http://trac-hacks.org/changeset/latest/wikiextrasplugin?old_path=/&filename=wikiextrasplugin&format=zip here].


== Source ==

You can check out
[http://trac-hacks.org/wiki/WikiExtrasPlugin WikiExtrasPlugin] from
[http://trac-hacks.org/svn/wikiextrasplugin here] using Subversion, or
[http://trac-hacks.org/browser/wikiextrasplugin browse the source] with Trac.


== Configuration ==

Activate the plugin:
{{{
[components]
tracwikiextras.* = enabled
}}}

The built in documentation of the plugin explains the configuration thoroughly.
Following examples are provided as an overview of the customization
capabilities of the plugin.

Configure boxes ''(showing default configuration)'':
{{{
[wikiextras]
rbox_width = 300
shadowless_boxes = false
wide_toc = false
}}}

Configure icons ''(showing default configuration)'':
{{{
[wikiextras]
icon_limit = 32
showicons_limit = 96
shadowless_icons = false
}}}

Configure smileys ''(example)'':
{{{
[wikiextras-smileys]
_remove_defaults = true
smiley = :-) :)
smiley-wink = ;-) ;)
}}}

Configure attentional phrases ''(showing default configuration)'':
{{{
[wikiextras]
fixme_phrases = BUG, FIXME
todo_phrases = REVIEW, TODO
done_phrases = DONE, DEBUGGED, FIXED, REVIEWED
}}}

Configure symbols ''(example)'':
{{{
[wikiextras-symbols]
_remove_defaults = true
&laquo; = <<
&raquo; = >>
&hearts; = <3
}}}

[http://trac-hacks.org/wiki/WikiGoodiesPlugin WikiGoodiesPlugin] refugees might 
find the following compatibility definitions useful:
{{{
[wikiextras-smileys]
exclamation--frame = /!\
exclamation-diamond-frame = <!>
thumb = {DN} {!OK}
thumb-up = {UP} {OK}
star = {*}
star-empty = {o}
light-bulb = (!)
priority1 = {p1} {P1}
priority2 = {p2} {P2}
priority3 = {p3} {P3}
}}}

== Example ==

There are 3 macros that can be used to show detailed instructions to wiki
authors on how to use some of these features, suitable to be placed on one wiki
page each:
 * !WikiBoxes
{{{
[[AboutWikiBoxes]]
}}}
 * !WikiIcons
{{{
[[AboutWikiIcons]]
}}}
 * !WikiPhrases
{{{
[[AboutWikiPhrases]]
}}}

Please also see the built in plugin documentation presented in the plugin admin
panel of your Trac environment.


== Author / Contributors ==

'''Author:''' [http://trac-hacks.org/wiki/mrelbe mrelbe] [[BR]]
'''Maintainer:''' [http://trac-hacks.org/wiki/mrelbe  mrelbe] [[BR]]
'''Contributors:''' [http://trac-hacks.org/wiki/cboos cboos] [[BR]]

This plugin is based on the
[http://trac-hacks.org/wiki/WikiGoodiesPlugin WikiGoodiesPlugin] by
[http://trac-hacks.org/wiki/cboos cboos]. [[BR]]
Also, kudos to [wiki:cboos] (again) for the icon wiki markup idea: `(|name|)`
